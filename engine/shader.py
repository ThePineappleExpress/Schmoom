from OpenGL.GL import *

class ShaderLoader:
    def __init__(self, vert_path=None, frag_path=None):
        vert_id = self._compile_shader(vert_path, GL_VERTEX_SHADER)
        frag_id = self._compile_shader(frag_path, GL_FRAGMENT_SHADER)
        self.program = glCreateProgram()
        glAttachShader(self.program, vert_id)
        glAttachShader(self.program, frag_id)
        glLinkProgram(self.program)
        success = glGetProgramiv(self.program, GL_LINK_STATUS)
        if not success:
            error = glGetProgramInfoLog(self.program)
            print(f"Shader compile error: {error}")

    def _compile_shader(self, path, shader_type):
        with open(path, 'r') as f:
            source_string = f.read()
        shader_id = glCreateShader(shader_type)
        glShaderSource(shader_id, source_string)
        glCompileShader(shader_id)   
        success = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
        if not success:
            error = glGetShaderInfoLog(shader_id)
            print(f"Shader compile error: {error}")
        return shader_id 
        
    def use(self):
        glUseProgram(self.program)

    def set_uniform(self, name, value):
        loc = glGetUniformLocation(self.program, name)
        if isinstance(value, float):
            glUniform1f(loc, value)
        elif isinstance(value, int):
            glUniform1i(loc, value)
        elif len(value) == 2:
            glUniform2f(loc, *value)
        elif len(value) == 3:
            glUniform3f(loc, *value)
        elif len(value) == 4:
            glUniform4f(loc, *value)
