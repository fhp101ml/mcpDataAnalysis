from src.core.graph import workflow
import asyncio

async def generate_graph_png():
    try:
        # Se compila sin la memoria para inspeccionar unicamente los nodos y edges
        app_graph = workflow.compile()
        png_bytes = app_graph.get_graph().draw_mermaid_png()
        
        with open("kdd_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Grafo guardado exitosamente en kdd_graph.png")
    except Exception as e:
        print(f"Error generando la imagen PNG: {e}")

if __name__ == "__main__":
    asyncio.run(generate_graph_png())
