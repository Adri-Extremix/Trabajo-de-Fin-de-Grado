import sys
import os
import unittest.main

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
import glob
import subprocess
from pprint import pprint
from back.debugger import Debugger

class TestDebugger(unittest.TestCase):

    

    @classmethod
    def setUpClass(cls) -> None:
        cls.c_files = list(reversed(glob.glob("../examples/*.c")))
        cls.binary_files = []
        for c_file in cls.c_files:
            output_name = os.path.splitext(c_file)[0] + ".out"
            subprocess.run(["gcc", c_file, "-o", output_name],
               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cls.binary_files.append("./" + output_name)

    def test_parse_code1(self):
        debugger = Debugger(self.c_files[0], self.binary_files[0])
        functions = debugger.parse_code()
        self.assertEqual(functions, {"main": (20, 46), "greet": (49, 52)
                                     , "add": (55, 60), "printArray": (63, 71)}, "Functions in code 1 are not parsed correctly")

    def test_parse_code2(self):
        debugger = Debugger(self.c_files[1], self.binary_files[1])
        functions = debugger.parse_code()
        self.assertEqual(functions, {"print_row": (19, 28), "main": (30, 54)}, "Functions in code 2 are not parsed correctly")

    @staticmethod
    def normalize_indentation(code):
        lines = code.splitlines()
        normalized_lines = [line.lstrip() for line in lines]
        return "\n".join(normalized_lines)


    def test_get_main_code1(self):
        self.maxDiff = None
        debugger = Debugger(self.c_files[0], self.binary_files[0])
        code = self.normalize_indentation(debugger.get_code_function("main"))
        expected_code =self.normalize_indentation("""int main() {
                            pthread_t thread1, thread2, thread3;

                            // Create thread for greet function
                            pthread_create(&thread1, NULL, greet, NULL);

                            // Create thread for add function
                            AddArgs addArgs = { 5, 3, 0 };
                            pthread_create(&thread2, NULL, add, &addArgs);

                            // Create thread for printArray function
                            int arr[] = { 1, 2, 3, 4, 5 };
                            PrintArrayArgs printArrayArgs = { arr, 5 };
                            pthread_create(&thread3, NULL, printArray, &printArrayArgs);

                            // Wait for threads to finish
                            pthread_join(thread1, NULL);
                            pthread_join(thread2, NULL);
                            pthread_join(thread3, NULL);

                            // Print the result of add function
                            printf("Sum: %d\\n", addArgs.result);

                            int result = 0;

                            return 0;
                        }""")
        self.assertEqual(code, expected_code, "Main function in code 1 is not parsed correctly")

    def test_get_main_code2(self):
        self.maxDiff = None
        debugger = Debugger(self.c_files[1], self.binary_files[1])
        code = self.normalize_indentation(debugger.get_code_function("main"))
        expected_code = self.normalize_indentation("""int main() {
                            pthread_t threads[M]; // Array para almacenar identificadores de los hilos
                            int row_indices[M];   // Array para pasar índices de las filas a los hilos

                            // Crear un hilo para cada fila
                            for (int i = 0; i < M; i++) {
                                row_indices[i] = i; // Asignar el índice de la fila
                                if (pthread_create(&threads[i], NULL, print_row, &row_indices[i]) != 0) {
                                    perror("Error creando hilo");
                                    return 1;
                                }
                            }

                            // Esperar a que todos los hilos terminen
                            for (int i = 0; i < M; i++) {
                                if (pthread_join(threads[i], NULL) != 0) {
                                    perror("Error esperando hilo");
                                    return 1;
                                }
                            }

                            printf("Todos los hilos han terminado.\\n");
                            printf("¿Han términado en orden?");
                            return 0;
                        }""")
        self.assertEqual(code,expected_code, "Main function in code 2 is not parsed correctly")
    
    def test_run_code(self):
        debugger = Debugger(self.c_files[0], self.binary_files[0])
        debugger.run()
        self.assertEqual(debugger.threads, {}, "Run method in code 1 is not working correctly")
            
