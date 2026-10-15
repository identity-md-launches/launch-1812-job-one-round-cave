#!/usr/bin/env python3
"""Check JSON Lines structure and explicit cross-row scalar uniqueness offline."""
import argparse
from decimal import Decimal, DecimalException
import json
from pathlib import Path
import re
import sys
import types

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    reader = bounded_module()
    path = Path(__file__).absolute().parent.parent / 'jsonl-contract' / 'check.py'
    module = types.ModuleType('unique_jsonl_contract')
    module.__file__ = str(path)
    exec(compile(reader.read_bytes(path.relative_to(Path.cwd()).as_posix()), str(path), 'exec'), module.__dict__)
    _, source, engine, rules = module.dependencies()
    return reader, module, source, engine, rules


def pointers_checked(pointers):
    if not 1 <= len(pointers) <= 16 or len(set(pointers)) != len(pointers):
        raise ValueError('supply 1 to 16 distinct JSON Pointers')
    for pointer in pointers:
        if len(pointer) > 1024 or (pointer and not pointer.startswith('/')) or re.search(r'~(?![01])', pointer):
            raise ValueError('invalid JSON Pointer (empty string selects the root)')
    return pointers


def resolve(value, pointer):
    for token in pointer.split('/')[1:] if pointer else []:
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif isinstance(value, list) and re.fullmatch(r'0|[1-9][0-9]*', token) and len(token) < 10 and int(token) < len(value):
            value = value[int(token)]
        else:
            raise KeyError(pointer)
    return value


def scalar_key(value, token):
    # Numeric equality uses the original decimal token, never rounded floats.
    # Boolean, number, string and null are separate domains; 1 and 1.0 agree.
    if isinstance(value, (dict, list)):
        raise ValueError('uniqueness requires a scalar value')
    if value is None:
        return ('null', None)
    if isinstance(value, bool):
        return ('boolean', value)
    if isinstance(value, str):
        return ('string', value)
    try:
        number = Decimal(token)
        hash(number)
    except (DecimalException, OverflowError, ValueError) as exc:
        raise ValueError('numeric token exceeds exact comparison limits') from exc
    return ('number', number)


def inspect(reader, framing, source, engine, rules, contract_name, document_name,
            pointers, contract_sha256=None, document_sha256=None):
    pointers = pointers_checked(pointers)
    captured = {}
    class Capture:
        def read_bytes(self, name):
            if name not in captured:
                captured[name] = reader.read_bytes(name)
            return captured[name]
    structural = framing.inspect(Capture(), source, engine, rules, contract_name,
                                 document_name, contract_sha256, document_sha256)
    text = captured[document_name].decode('utf-8')
    bodies = text.split('\n')
    if text.endswith('\n'):
        bodies.pop()
    seen = {p: {} for p in pointers}
    errors, skipped, char_start = [], [], 0
    for row, body in zip(structural['rows'], bodies):
        if row['status'] == 'malformed':
            skipped.append(row['line'])
        else:
            document = source.Source(body.encode('utf-8'), document_name)
            for pointer in pointers:
                # Missing deep paths anchor the nearest existing container.
                anchor = pointer
                while anchor not in document.values:
                    anchor = anchor.rsplit('/', 1)[0]
                location = document.location(anchor)
                framing.shift_location(location, row['line'], row['byte_start'], char_start)
                error = {'line': row['line'], 'pointer': pointer, 'document_source': location}
                try:
                    value = resolve(document.value, pointer)
                except KeyError:
                    error.update(kind='missing_value', anchor_pointer=anchor)
                    errors.append(error)
                    continue
                try:
                    start, end = document.values[pointer]
                    key = scalar_key(value, body[start:end])
                except ValueError as exc:
                    error.update(kind='non_scalar' if isinstance(value, (dict, list)) else 'unsupported_number', message=str(exc))
                    errors.append(error)
                    continue
                if key in seen[pointer]:
                    error.update(kind='duplicate_value', first=seen[pointer][key])
                    errors.append(error)
                else:
                    seen[pointer][key] = {'line': row['line'], 'document_source': location}
        char_start += len(body) + 1
    valid = structural['valid'] and not errors
    return {'valid': valid, 'complete': True,
            'status': 'valid' if valid else 'rejected',
            'structural': structural,
            'uniqueness': {'pointers': pointers, 'valid': not errors and not skipped,
                           'checked_rows': len(bodies)-len(skipped),
                           'skipped_malformed_lines': skipped,
                           'error_count': len(errors), 'errors': errors,
                           'equality': 'exact decimal numeric equality; booleans, strings and null are separate types; each pointer checked independently'}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    parser.add_argument('document')
    parser.add_argument('--unique', action='append', required=True, help='JSON Pointer; repeat for independent unique fields')
    parser.add_argument('--contract-sha256')
    parser.add_argument('--document-sha256')
    args = parser.parse_args(argv)
    try:
        deps = dependencies()
        result = inspect(*deps, args.contract, args.document, args.unique,
                         args.contract_sha256, args.document_sha256)
        output = deps[1].encode(result)
        sys.stdout.write(output)
        return 2 if result['structural']['summary']['malformed'] else (0 if result['valid'] else 1)
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        sys.stderr.write(json.dumps({'valid': False, 'complete': False,
                                     'error': str(exc)[:1000]}, ensure_ascii=True)+'\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
