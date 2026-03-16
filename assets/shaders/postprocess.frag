#version 330 core
in vec2 vUV;
out vec4 FragColor;

uniform sampler2D u_scene;   // the FBO texture
uniform sampler2D u_depth;    // the depth texture
uniform float u_damage;

void main() {
    float dist = texture(u_depth, vUV).r;
    
    vec2 u_c = vec2(0.5,0.5);
    vec4 scene = texture(u_scene, vUV);
    float vignette = length(vUV - u_c) * 0.7; // 0 at center, ~1 at corners
    scene = mix(scene, vec4(1.0, 0.0, 0.0, 1.0), u_damage);
    gl_FragColor = mix(scene * dist, vec4(0.,0.,0.,1.), (vignette*2.0));
}