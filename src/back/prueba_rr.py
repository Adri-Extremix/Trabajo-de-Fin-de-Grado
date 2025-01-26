from pygdbmi.gdbcontroller import GdbController
from pprint import pprint
def main():
    # Inicia GDB con rr replay y modo MI3
    gdb = GdbController(command=["rr", "replay", "--interpreter=mi3"])

    # Envía comandos iniciales
    print("Iniciando replay...")
    gdb.write("break main")  # Configura un breakpoint
    respuesta = gdb.write("-exec-run", timeout_sec=5)  # Ejecuta el programa

    # Procesa las respuestas
    pprint(respuesta)
if __name__ == "__main__":
    main()
