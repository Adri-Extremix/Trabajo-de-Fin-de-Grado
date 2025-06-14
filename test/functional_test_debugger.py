from calendar import c
from pdb import run
import sys
import os
import time
import glob
# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from docker.debugger import Debugger
from pprint import pprint
import subprocess

c_files = list(sorted(glob.glob("../examples/*.c")))
binary_files = []


def setup():
    for c_file in c_files:
        binary_file = c_file.replace('.c', '.o')
        compile_cmd = ['gcc', '-g', '-O0', c_file, '-o', binary_file]
        subprocess.check_call(compile_cmd)
        binary_files.append(binary_file)
        print(f"Compilado {c_file} -> {binary_file}")

def clean():
    for binary_file in binary_files:
        os.remove(binary_file)
        print(f"Eliminado {binary_file}")


def run_breakpoint_code1():
    debugger = Debugger(c_files[0], binary_files[0], rr=False)
    debugger.set_breakpoint(50)
    result = debugger.run()

    print("Historial de variables globales después de ejecutar hasta el primer breakpoint:")
    pprint(result["globals"])

    threads = result["threads"]
    assert "1" in threads.keys(), "El hilo '1' no se encontró en el resultado"
    assert "2" in threads.keys(), "El hilo '2' no se encontró en el resultado"

    assert threads["1"]["function"] == "main", f"El hilo '1' no se detuvo en la función 'main', se detuvo en la función {threads['1']['function']}"

    assert threads["2"]["line"] == "50", f"El hilo '2' no se detuvo en la línea 50, se detuvo en la línea {threads['2']['line']}"
    assert threads["2"]["function"] == "greet", f"El hilo '2' no se detuvo en la función 'greet', se detuvo en la función {threads['2']['function']}"

def run_breakpoint_code2():
    debugger = Debugger(c_files[1], binary_files[1], rr=False)
    debugger.set_breakpoint(20)
    result = debugger.run()
    print("Historial de variables globales después de ejecutar hasta el primer breakpoint:")
    pprint(result["globals"])

    threads = result["threads"]
    assert "1" in threads.keys(), "El hilo '1' no se encontró en el resultado"

    assert threads["1"]["function"] == "main", f"El hilo '1' no se detuvo en la función 'main', se detuvo en la función {threads['1']['function']}"

    found = any(info.get("line") == "20" for info in threads.values())
    assert found, "Ningún hilo se ha parado en la línea 20"

def continue_breakpoint_code1():
    debugger = Debugger(c_files[0], binary_files[0], rr=False)
    debugger.set_breakpoint(28)
    debugger.set_breakpoint(70)
    
    result_run = debugger.run()
    print("Historial de variables globales después de ejecutar hasta el primer breakpoint:")
    pprint(result_run["globals"])

    threads_run = result_run["threads"]
    assert len(threads_run) == 1, f"Se esperaba solo 1 hilo, se encontraron {len(threads_run)}"

    assert "1" in threads_run, "La clave '1' no se encontró en el resultado"

    assert threads_run["1"]["function"] == "main", f"El hilo '1' no se detuvo en la función 'main', se detuvo en la función {threads_run['1']['function']}"

    assert threads_run["1"]["line"] == "28", f"El hilo '1' no se detuvo en la línea 28, se detuvo en la línea {threads_run['1']['line']}"



    result_continue = debugger.continue_execution()
    print("Historial de variables globales después de continuar:")
    pprint(result_continue["globals"])

    threads_continue = result_continue["threads"]
    assert len(threads_continue) == 2, f"Se esperaban 2 hilos, se encontraron {len(threads_continue)}"

    assert "1" in threads_continue, "La clave '1' no se encontró en el resultado"
    assert "4" in threads_continue, "La clave '4' no se encontró en el resultado"

    assert threads_continue["1"]["function"] == "main", f"El hilo '1' no se detuvo en la función 'main', se detuvo en la función {threads_continue['1']['function']}"

    assert threads_continue["4"]["function"] == "printArray", f"El hilo '4' no se detuvo en la función 'printArray', se detuvo en la función {threads_continue['4']['function']}"

    assert threads_continue["4"]["line"] == "70", f"El hilo '4' no se detuvo en la línea 70, se detuvo en la línea {threads_continue['4']['line']}"

def continue_breakpoint_code2():
    debugger = Debugger(c_files[1], binary_files[1], rr=False)
    debugger.set_breakpoint(22)
    debugger.set_breakpoint(41)
    result_run = debugger.run()

    threads_run = result_run["threads"]
    assert len(threads_run) == 7, f"Se esperaban solo 7 hilos, se encontraron {len(threads_run)}"

    result_continue = debugger.continue_execution()
    pprint(result_continue["globals"])

    threads_continue = result_continue["threads"]
    assert len(threads_continue) == 7, f"Se esperaban que se mantuvieran los 7 hilos, pero se encontraron {len(threads_continue)}"

def reversing_breakpoint_code1():
    debugger = Debugger(c_files[0], binary_files[0], rr=True)
    debugger.set_breakpoint(28)
    debugger.set_breakpoint(70)
    result_run = debugger.run()
    debugger.continue_execution()
    result_reverse = debugger.reverse_continue()
    pprint(result_reverse["globals"])


    assert result_run == result_reverse, "El resultado de la ejecución al breakpoint 28 y el resultado de la reversión a ese mismo breakpoint no son iguales"

def reversing_breakpoint_code2():
    debugger = Debugger(c_files[1], binary_files[1], rr=True)
    debugger.set_breakpoint(22)
    debugger.set_breakpoint(41)
    result_run = debugger.run()
    debugger.continue_execution()
    result_reverse = debugger.reverse_continue()
    pprint(result_reverse["globals"])

    
    assert result_run == result_reverse, "El resultado de la ejecución al breakpoint 22 y el resultado de la reversión a ese mismo breakpoint no son iguales"

def stepping_over_code1():
    debugger = Debugger(c_files[0],binary_files[0], rr=False)
    debugger.set_breakpoint(27)
    debugger.run()

    result = debugger.step_over("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "28", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la líneea 28. Se encuentra en la línea {threads['1']['line']}"

def stepping_over_code2():
    debugger = Debugger(c_files[1],binary_files[1], rr=False)
    debugger.set_breakpoint(44)
    debugger.run()

    result = debugger.step_over("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "45", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la líneea 45. Se encuentra en la línea {threads['1']['line']}"

def stepping_over_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=False)
    debugger.set_breakpoint(28)
    debugger.run()
    result = debugger.step_over("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"
    assert threads["1"]["line"] == "30", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la líneea 30. Se encuentra en la línea {threads['1']['line']}"
    
def stepping_out_of_a_function_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=False)
    debugger.set_breakpoint(6)
    debugger.run()
    result = debugger.step_out("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "31", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la línea 31. Se encuentra en la línea {threads['1']['line']}"

def stepping_out_of_main_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=False)
    debugger.set_breakpoint(30)
    debugger.run()
    result = debugger.step_out("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "31", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la línea 31. Se encuentra en la línea {threads['1']['line']}"

def stepping_out_of_other_file_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=False)
    debugger.set_breakpoint(19)
    debugger.run()
    result = debugger.step_out("2")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["2"]["function"] == "hilo_funcion", f"El hilo 2 no se encuentra en la función hilo_funcion, se encuentra en la funcion {threads['2']['function']}"

    assert threads["2"]["line"] == "20", f"El hilo 2 no ha realizado correctamente el step, no encontrandose en la línea 20. Se encuentra en la línea {threads['2']['line']}"


def stepping_into_a_function_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=False)
    debugger.set_breakpoint(30)
    debugger.run()
    result = debugger.step_into("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "funcion1", f"El hilo 1 no se encuentra en la función funcion1, se encuentra en la función {threads['1']['function']}"

    assert threads["1"]["line"] == "6", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la línea 6. Se encuentra en la línea {threads['1']['line']}"

def stepping_into_a_not_function_code1():
    debugger = Debugger(c_files[0],binary_files[0], rr=False)
    debugger.set_breakpoint(66)
    debugger.run()
    result = debugger.step_into("4")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["4"]["function"] == "printArray", f"El hilo 4 no se encuentra en la función printArray, se encuentra en la función {threads['4']['function']}"

    assert threads["4"]["line"] == "67", f"El hilo 4 no ha realizado correctamente el step, no encontrandose en la línea 67. Se encuentra en la línea {threads['4']['line']}"

def stepping_into_a_other_file_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=False)
    debugger.set_breakpoint(28)
    debugger.run()
    result = debugger.step_into("1")
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", f"El hilo 1 no se encuentra en la función funcion1, se encuentra en la función {threads['1']['function']}"

    assert threads["1"]["line"] == "30", f"El hilo 1 no ha realizado correctamente el step, no encontrandose en la línea 30. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_over_code1():
    debugger = Debugger(c_files[0],binary_files[0], rr=True)
    debugger.set_breakpoint(27)
    debugger.run()
    debugger.step_over("1")
    result = debugger.reverse_step_over()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "27", f"El hilo 1 no ha realizado correctamente el reverse step over, no encontrandose en la línea 27. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_over_code2():
    debugger = Debugger(c_files[1],binary_files[1], rr=True)
    debugger.set_breakpoint(44)
    debugger.run()
    debugger.step_over("1")
    result = debugger.reverse_step_over()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "44", f"El hilo 1 no ha realizado correctamente el reverse step over, no encontrandose en la línea 44. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_over_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=True)
    debugger.set_breakpoint(28)
    debugger.run()
    debugger.step_over("1")
    result = debugger.reverse_step_over()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"
    assert threads["1"]["line"] == "28", f"El hilo 1 no ha realizado correctamente el reverse step over, no encontrandose en la línea 28. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_out_of_a_function_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=True)
    debugger.set_breakpoint(6)
    debugger.run()
    debugger.step_out("1")
    result = debugger.reverse_step_out()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "funcion1", f"El hilo 1 no se encuentra en la función funcion1, se encuentra en la función {threads['1']['function']}"

    assert threads["1"]["line"] == "6", f"El hilo 1 no ha realizado correctamente el reverse step out, no encontrandose en la línea 6. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_out_of_main_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=True)
    debugger.set_breakpoint(30)
    debugger.run()
    debugger.step_out("1")
    result = debugger.reverse_step_out()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "30", f"El hilo 1 no ha realizado correctamente el reverse step out, no encontrandose en la línea 30. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_out_of_other_file_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=True)
    debugger.set_breakpoint(19)
    debugger.run()
    debugger.step_out("2")
    result = debugger.reverse_step_out()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["2"]["function"] == "hilo_funcion", f"El hilo 2 no se encuentra en la función worker_function, se encuentra en la función {threads['2']['function']}"

    assert threads["2"]["line"] == "19", f"El hilo 2 no ha realizado correctamente el reverse step out, no encontrandose en la línea 19. Se encuentra en la línea {threads['2']['line']}"

def reverse_stepping_into_a_function_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=True)
    debugger.set_breakpoint(30)
    debugger.run()
    debugger.step_into("1")
    result = debugger.reverse_step_into()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "30", f"El hilo 1 no ha realizado correctamente el reverse step into, no encontrandose en la línea 30. Se encuentra en la línea {threads['1']['line']}"

def reverse_stepping_into_a_other_file_code3():
    debugger = Debugger(c_files[2],binary_files[2], rr=True)
    debugger.set_breakpoint(28)
    debugger.run()
    debugger.step_into("1")
    result = debugger.reverse_step_into()
    pprint(result["globals"])

    threads = result["threads"]
    assert threads["1"]["function"] == "main", "El hilo 1 no se encuentra en la función main"

    assert threads["1"]["line"] == "28", f"El hilo 1 no ha realizado correctamente el reverse step into, no encontrandose en la línea 28. Se encuentra en la línea {threads['1']['line']}"
def test():
    debugger = Debugger(c_files[0], binary_files[0], rr=False)
    debugger.set_breakpoint(50)
    result = debugger.run()
    pprint(result)
    result = debugger.step_over("2")
    pprint(result)
    result = debugger.step_over("2")
    pprint(result)


if __name__ == "__main__":

    start_time = time.time()

    print("\033[93m\n ----------------- Realizando el setup ----------------- \n\033[0m")
    setup()
    print("\033[93m\n ----------------- Ejecutando tests ----------------- \n\033[0m")
    # Tests de stepping
    tests = [
        run_breakpoint_code1,
        run_breakpoint_code2,
        continue_breakpoint_code1,
        continue_breakpoint_code2,
        stepping_over_code1,
        stepping_over_code2,
        stepping_over_code3,
        stepping_out_of_a_function_code3,
        stepping_out_of_main_code3,
        stepping_out_of_other_file_code3,
        stepping_into_a_function_code3,
        stepping_into_a_not_function_code1,
        stepping_into_a_other_file_code3
    ]
    #tests = [stepping_over_code1, stepping_over_code2, stepping_over_code3,
    #         stepping_out_of_a_function_code3, stepping_out_of_main_code3, stepping_out_of_other_file_code3,
    #         stepping_into_a_function_code3, stepping_into_a_not_function_code1, stepping_into_a_other_file_code3]
    passed = []
    failed = []
    errors = []
    
    for test in tests:
        try:
            print(f"Ejecutando test {test.__name__}")
            test()
            print("\033[92m" + f"{test.__name__}: OK" + "\033[0m\n")
            passed.append(test.__name__)
        except AssertionError as ae:
            print("\033[91m" + f"{test.__name__}: Falló - {ae}\n" + "\033[0m")
            failed.append((test.__name__, str(ae)))
        # except Exception as e:
        #     print("\033[91m" + f"{test.__name__}: Error inesperado - {e}\n" + "\033[0m")
        #     errors.append((test.__name__, str(e)))
    
    print("\033[93m----------------- Resumen de tests ----------------- \n\033[0m")

    print(f"Pasaron {len(passed)} tests: {passed}")
    if failed:
        print("Fallaron {len(failed)} tests:")
        for test_name, msg in failed:
            print(f" - {test_name}: {msg}")
    if errors:
        print("Errores inesperados:")
        for test_name, msg in errors:
            print(f" - {test_name}: {msg}")

    print("\033[93m\n ----------------- Limpiando archivos ----------------- \n\033[0m")

    clean()

    elapsed_time = round((time.time() - start_time) / 60,4)
    print(f"\033[93m\n ----------------- Tiempo total de ejecución: {elapsed_time} minutos ----------------")
