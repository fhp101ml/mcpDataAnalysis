import pytest
from src.api.mcp_tools import SandboxMCPTool

@pytest.mark.asyncio
async def test_sandbox_success():
    code = "print('Hello from isolated Sandbox')"
    response = await SandboxMCPTool.execute_python_code(code)
    
    assert response.success is True
    assert "Hello from isolated Sandbox" in response.data["stdout"]
    assert response.error is None

@pytest.mark.asyncio
async def test_sandbox_syntax_error():
    # Código con mala sintaxis intencionada
    code = "prnt('Esto va a fallar'"
    response = await SandboxMCPTool.execute_python_code(code)
    
    assert response.success is False
    assert response.error is not None
    assert "SyntaxError" in response.data["stderr"] or "NameError" in response.data["stderr"]
