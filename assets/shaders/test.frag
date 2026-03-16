#version 330 core
in vec2 vUV;                          // received from vertex shader
out vec4 FragColor;                   // output pixel color
uniform sampler2D u_map_tex;          // map texture
void main() {
    float tile = texture(u_map_tex, vUV).r * 255.0; // sample tile type from map texture
    FragColor = vec4(vUV.x, vUV.y, 0.0, 1.0);  // gradient test
}