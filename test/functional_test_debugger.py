import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from back.debugger import Debugger
from pprint import pprint

def breakpoint_code1():
    debugger = Debugger("../examples/prueba2.c", "../examples/prueba2.o", rr=False)
    print("Colocando breakpoint")
    debugger.set_breakpoint(22)
    print("Colocando breakkpoint")
    debugger.set_breakpoint(33)
    print("Ejecutando el programa")
    pprint(debugger.run())

    print("Continuando la ejecución")
    pprint(debugger.continue_execution())
    print("Volviendo al anterior breakpoint")
    result = debugger.reverse_continue()
    pprint(result)
    # Reemplaza "expected_result" por el resultado esperado, por ejemplo:
    expected_result = {
        'clave1': 'valor1',
        'clave2': 'valor2'
    }
    # Al comparar diccionarios con == se verifica que tengan las mismas claves y valores
    assert result == expected_result, f"El resultado {result} no coincide con lo esperado {expected_result}"

def breakpoint_code2():
    debugger = Debugger("../examples/prueba1.c", "../examples/prueba1.o", rr=False)
    print("Colocando breakpoint")
    debugger.set_breakpoint(22)
    print("Colocando breakkpoint")
    debugger.set_breakpoint(33)
    print("Ejecutando el programa")
    pprint(debugger.run())

    print("Continuando la ejecución")
    pprint(debugger.continue_execution())
    print("Volviendo al anterior breakpoint")
    result = debugger.reverse_continue()
    pprint(result)
    # Reemplaza "expected_result" por el resultado esperado, por ejemplo:
    expected_result = {
        'clave1': 'valor1',
        'clave2': 'valor2'
    }
    # Al comparar diccionarios con == se verifica que tengan las mismas claves y valores
    assert result == expected_result, f"El resultado {result} no coincide con lo esperado {expected_result}"


if __name__ == "__main__":
    tests = [breakpoint_code1, breakpoint_code2]
    passed = []
    failed = []
    errors = []
    
    for test in tests:
        try:
            test()
            print(f"{test.__name__}: OK")
            passed.append(test.__name__)
        except AssertionError as ae:
            print(f"{test.__name__}: Falló - {ae}")
            failed.append((test.__name__, str(ae)))
        except Exception as e:
            print(f"{test.__name__}: Error inesperado - {e}")
            errors.append((test.__name__, str(e)))
    
    print("\nResumen de tests:")
    print(f"Pasaron {len(passed)} tests: {passed}")
    if failed:
        print("Fallaron {len(failed)} tests:")
        for test_name, msg in failed:
            print(f" - {test_name}: {msg}")
    if errors:
        print("Errores inesperados:")
        for test_name, msg in errors:
            print(f" - {test_name}: {msg}")
