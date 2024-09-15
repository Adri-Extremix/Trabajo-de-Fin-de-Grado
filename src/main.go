package main

import (
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

func main() {
    // Crear la aplicación
    a := app.New()
    w := a.NewWindow("Editor de Código")

    // Crear un widget de entrada de texto multilínea
    codeEntry := widget.NewMultiLineEntry()
    codeEntry.SetPlaceHolder("Escribe tu código aquí...")
    // Crear un botón para compilar o ejecutar el código
    runButton := widget.NewButton("Ejecutar", func() {
        // Aquí puedes agregar la lógica para ejecutar el código o hacer alguna acción
        code := codeEntry.Text
        // Por ahora, solo se imprimirá el código ingresado en la consola
        println("Código ingresado:", code)
    })

    // Crear un contenedor que contenga el campo de texto y el botón
    content := container.NewVBox(codeEntry, runButton)

    // Asignar el contenedor a la ventana y mostrarla
    w.SetContent(content)
    w.Resize(fyne.NewSize(400, 300))  // Tamaño de la ventana
    w.ShowAndRun()
}
