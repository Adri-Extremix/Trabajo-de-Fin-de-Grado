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

    .very-small {
        font-size: 0.5em;
    }

    .small {
        font-size: 0.7em;
    }
    .medium {
        font-size: 0.9em;
    }
    .large {
        font-size: 1.3em;
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
    .left-align {
        text-align: left;
        display: block;
    }

    img[alt~="center"] {
        display: block;
        margin: 0 auto;
    }

    .margin-top {
        margin-top: 20px;
    }

    .border-radius {
        border-radius: 5px;
    }
    
    .tools-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 40px;
        align-items: start;
        justify-items: center;
        margin: 20px 0;
    }
    
    .tool-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .tool-name {
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 15px;
    }
    
    .tool-image {
        width: 240px;
        height: 240px;
        object-fit: contain;
        border-radius: 8px;
    }

    .flex_column {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .flex_row {
        display: flex;
        flex-direction: row;
        justify-content: space-around;
        align-items: center;
        gap: 40px;
    }

---
<!-- _header: "" -->
<!-- _footer: "" -->
<!-- _paginate: false -->

# Trabajo de Fin de Grado
##### Herramienta Didáctica para la Programación Concurrente

<span class="small">Autor: Adrián Fernández Galán</span>
<span class="small">Tutor: Alejandro Calderón Mateos</span>

<div class="margin-top">
    <img src="./images/logo.png" class="border-radius" height="100px" alt="Logo">
</div>

---
### <span class="left-align"> Contenidos </span>
<span class="medium">

1. Introducción: Motivación y Objetivos
2. Estado del Arte
3. Planificación y Presupuesto
4. Diseño
5. Demo
6. Conclusiones y Trabajo Futuro

</span>

---
# 1. Introducción

---
<!-- _header: "1. Introducción" -->
![bg right:40% 80%](./images/linux.png)
# <span class="left-align">Motivación</span>
<br>

- **Sistemas Operativos**

---
<!-- _header: "1. Introducción" -->
![bg right:45% 90%](./images/Hilos.svg)
#### Motivación

- Desarrollo concurrente **frustrante**
- Conceptos **complicados**
- Ejecución de hilos **poco transparente**


---
<!-- _header: "1. Introducción" -->

## Objetivos

Crear una herramienta que permita:
<br>

- **Desarrollar programas concurrentes en C**
- **Enfoque didáctico**
---

# 2. Estado del Arte  
---
<!-- _header: "2. Estado del Arte" -->
#### Herramientas Similares a la Propuesta

<div class="tools-grid">
    <div class="tool-item">
        <div class="tool-name">GDB</div>
        <img src="./images/GDB.png" alt="GDB" class="tool-image">
    </div>
    <div class="tool-item">
        <div class="tool-name">CLion</div>
        <img src="./images/CLion.png" alt="CLion" class="tool-image">
    </div>
    <div class="tool-item">
        <div class="tool-name">Seer</div>
        <img src="./images/Seer.png" alt="Seer" class="tool-image">
    </div>
</div>

---
![bg right:45% 95%](./images/grafico_comparacion.drawio.svg)
<!-- _header: "2. Estado del Arte" -->
#### ¿Qué aporta la propuesta?
- **Gratuita**
- **Fácil de usar**
- **Enfocada a la enseñanza**
- **Agnóstica**

---
<!-- _header: "2. Estado del Arte" -->
### ¿Cómo se va a conseguir esto?
- **Interfaz gráfica** fácil de usar
- **Visualización** del estado de los hilos
- **Controles** de la ejecución del programa
- **Abstracción** de los conceptos complejos
---

# 3. Planificación y Presupuesto

---

<!-- _header: "3. Planificación y Presupuesto" -->
![bg right:35% 45%](./mermaid/mi_diagrama.svg)
### Planificación

<span class="large left-align">**Metodología en Cascada**</span>
1. Planificación
2. Análisis
3. Diseño
4. Implementación
5. Evaluación
---
<!-- _header: "3. Planificación y Presupuesto" -->

![w:1000](./images/planificacion.png)

---
<!-- _header: "3. Planificación y Presupuesto" -->
### Presupuesto del Proyecto

| Concepto | Coste |
|:----------|-------:|
| Personal | 10.650,00 € |
| Equipamiento | 113,30 € |
| Costes indirectos | 1.939,00 € |
| **Total** | **12.702,30 €** |

---
### Oferta
<!-- _header: "3. Planificación y Presupuesto" -->
<span class="small">

| Concepto | Incremento | Coste Parcial | Coste Agregado |
|:----------|:-----------:|---------------:|----------------:|
| Coste del proyecto | 0% | 12.702,30 € | 12.702,30 € |
| Riesgo | 15% | 1.905,35 € | 14.607,65 € |
| Beneficio | 20% | 2.921,53 € | 17.529,18 € |
| Impuestos | 21% | 3.683,13 € | 21.212,31 € |
| **Total** | **56%** | **21.212,31 €** | **21.212,31 €** |

</span>

---
# 4. Diseño
---
##### Monolitico vs Distribuido
<!-- _header: "4. Diseño" -->
<div class="small left-align">

**Requisitos diferenciales**
- Herramienta **multiplataforma**
- Agnóstico a la **arquitectura** y al **SO**

</div>
<div class="flex_row">
    <div class="flex_column">
        <h4>Monolítico</h4>
        <img src="./mermaid/componentes_monolitico.svg" alt="Monolítico" width="500px">
    </div>
    <div class="flex_column">
        <h4>Distribuido</h4>
        <img src="./mermaid/componentes_distribuidos.svg" alt="Distribuido" width="500px">
    </div>
</div>

---
<!-- _header: "4. Diseño" -->
##### Arquitectura Cliente-Servidor
<div class="left-align small">

**Requisitos diferenciales**
- Entorno controlado → Contenedores ***Docker***

</div>
<div class="flex_row">
    <div class="flex_column">
        <h4 class="medium">Alternativa 1</h4>
        <img src="./mermaid/contenedores_servidor.svg" alt="Monolítico" width="500px">
    </div>
    <div class="flex_column">
        <h4 class="medium">Alternativa 2</h4>
        <img src="./mermaid/contenedores_proxy.svg" alt="Distribuido" width="500px">
    </div>
</div>

---
<!-- _header: "4. Diseño" -->
##### Diseño Final
<div class="small">

- **Contenedores**: *Python* + *Flask* + *WebSockets* + *GDB*
- **Proxy**: *Python*
- **Cliente**: *JavaScript* + *HTML* + *CSS*

</div>


![bg right:60% 100% invert](../img/componentes_TFG.drawio.svg)

---
# 5. Demo
---

# 6. Conclusiones y Trabajo Futuro
---

<!-- _header: "6. Conclusiones y Trabajo Futuro" -->
#### Conclusiones
- **Objetivos satisfechos**
    - Desarrollar programas concurrentes en C
    - Enfoque didáctico
- **Aprendizaje**
    - Arquitectura cliente-servidor
    - Arquitectura distribuida
    - *Dockerización* 
---

#### Trabajo Futuro
<!-- _header: "6. Conclusiones y Trabajo Futuro" -->
<span class="medium">

- **Mejora en la interfaz de usuario**
    - Diseño *responsive* y accesible
- **Aumento en las capacidades distribuidas**
    - DNS
    - Reinicio automático de contenedores
- **Nuevas funcionalidades de depuración**
    - Planificador de hilos personalizable
    - Soporte a más ficheros
    - Modificación de variables

</span>

---
# Gracias por su atención