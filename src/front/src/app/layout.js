export default function RootLayout({ children }) {
    return (
      <html lang="es">
        <head>
          <title>Concurrent Code</title>
          <meta name="description" content="Aplicación para código concurrente" />
        </head>
        <body>
          {children}
        </body>
      </html>
    );
  }