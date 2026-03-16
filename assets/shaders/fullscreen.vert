#version 330 core
layout(location = 0) in vec2 aPos;    // matches attribute 0 from your VAO
layout(location = 1) in vec2 aUV;     // matches attribute 1

out vec2 vUV;                         // passed to fragment shader

void main() {
    vUV = aUV;
    gl_Position = vec4(aPos, 0.0, 1.0);  // xy position, z=0, w=1
}