---
marp: true
theme: uncover
class: invert
size: 16:9
transition: fade # Transición global para el resto de diapositivas
paginate: true
header: "Herramienta Didáctica para la Programación Concurrente"
footer: "Adrián Fernández Galán"
style: |
    .small {
        font-size: 0.7em;
    }
    .medium {
        font-size: 0.9em;
    }
    .large {
        font-size: 1.2em;
    }

    .motivation-grid {
        display: grid;
        grid-template-columns: 50% 50%;
        grid-template-rows: repeat(3, 1fr);
        align-items: center;
        justify-items: start;
    }

    .image {
        width: 200px;
    }

    /* Estilo para el morphing de títulos */
    .morphing-title {
        view-transition-name: section-title; /* Nombre único para la transición */
    }

---
# Trabajo de Fin de Grado
##### Herramienta Didáctica para la Programación Concurrente

<span class="small">Autor: Adrián Fernández Galán</span>
<span class="small">Tutor: Alejandro Calderón Mateos</span>

---
![bg right:40% 80%](./images/linux.png)
# <span class="morphing-title">Motivación :rocket:</span>
<br>

- **Sistemas Operativos**

---
<br>

![bg right:45% 90%](./images/hilos.png)
#### <span class="morphing-title">Motivación :rocket:</span>

- Desarrollo concurrente **frustrante**
- Conceptos **complicados**
- Ejecución de hilos **poco transparente**


---
# <span class="morphing-title">Objetivos :pushpin:</span>
---
## <span class="morphing-title">Objetivos :pushpin:</span>

Crear una herramienta que permita:
<br>

- **Desarrollar programas concurrentes**
- **Enfoque didáctico**
---

# <span class="morphing-title">Herramientas Similares a la Propuesta :mag:</span>
---
#### <span class="morphing-title">Herramientas Similares a la Propuesta :mag:</span>
- **GDB**
- **Clion**
- **Seer**
---

#### ¿Qué aporta la propuesta? :bulb:
- **Gratuita**
- **Fácil de usar**
- **Enfocada a la enseñanza**
- **Agnóstica** (no dependiente del sistema y máquina)

---
[Imagen comparativa]

---

### ¿Cómo se va a conseguir esto? :wrench:
- **Interfaz gráfica** fácil de usar
- **Visualización** del estado de los hilos
- **Controles** de la ejecución del programa
- **Abstracción** de los conceptos complejos
---
# Diseño
---
### Diseño