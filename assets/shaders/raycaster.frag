#version 330 core
in vec2 vUV;
layout(location = 0) out vec4 FragColor;
layout(location = 1) out float FragDepth;
// Python sends these every frame
uniform vec2 u_player_pos;    // player x, y in world space
uniform float u_player_angle; // facing direction in radians
uniform vec2 u_resolution;    // screen width, height
uniform vec2 u_map_size;      // map width, height in tiles
uniform float u_fov;          // field of view in radians
uniform sampler2D u_map_tex;  // the map grid as a texture
uniform vec3 u_lights[128];    // x, y, brightness — up to 66 lights
uniform int u_num_lights;     // how many are active
uniform float u_bob_offset;          // head bobbing offset (0-1)
uniform float u_time;           // global u_time in seconds
vec3 brick_pattern(vec2 uv) {
    // Scale: 4 rows, 2 columns per wall tile
    vec2 scaled = uv * vec2(4.0, 8.0);
    
    // Offset every other row by half a brick width
    float row = floor(scaled.y);
    if (mod(row, 2.0) == 1.0) {
        scaled.x += 0.5;
    }
    
    // Get position within individual brick (0-1)
    vec2 brick_uv = fract(scaled);
    
    // Mortar lines: thin gaps between bricks
    float mortar = 0.05;
    float brick = step(mortar, brick_uv.x) * step(mortar, brick_uv.y);
    
    // Colors
    vec3 brick_color = vec3(0.6, 0.15, 0.1);   // reddish brown
    vec3 mortar_color = vec3(0.3, 0.3, 0.3);    // gray
    
    return mix(mortar_color, brick_color, brick);
}
mat2 rotate2D(float r) {
    return mat2(cos(r), sin(r), -sin(r), cos(r));
}
// Hash-based pseudo-random (returns 0.0–1.0)
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// Smooth value noise
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);  // smooth interpolation curve

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

vec3 stone_pattern(vec2 uv) {
    float n = noise(uv * 8.0) * 0.5
            + noise(uv * 16.0) * 0.25
            + noise(uv * 32.0) * 0.125;
    vec3 color = mix(vec3(1.0, 0.35, 0.35), vec3(0.6, 0.18, 0.15), n);
    return color;
}


vec3 metal_pattern(vec2 uv) {
    // Brushed metal: stretch noise horizontally
    float brushed = noise(uv * vec2(2.0, 32.0)) * 0.15;
    vec3 base = vec3(0.7, 0.12, 0.15) + brushed;

    // Rivets: grid of dots
    vec2 rivet_uv = fract(uv * 4.0) - 0.5;
    float rivet = 1.0 - smoothstep(0.05, 0.08, length(rivet_uv));
    base -= rivet * 0.2;

    return base;
}

vec3 door_pattern(vec2 uv) {
    vec3 wood = vec3(0.4, 0.25, 0.1);
    wood += noise(uv * vec2(2.0, 16.0)) * 0.1;  // wood grain

    // Frame border
    float border = 0.002;
    if (uv.x < border || uv.x > 1.0 - border || uv.y < border || uv.y > 1.0 - border)
        return vec3(0.25, 0.15, 0.05);  // darker frame

    return wood;
}

// Light calculation
float calc_lighting(vec2 hit_point) {
    float total_light = 0.2;  // ambient
    for (int li = 0; li < u_lights.length(); li++) {
        if (li >= u_num_lights) break;
        vec2 light_pos = u_lights[li].xy;
        float brightness = u_lights[li].z;

        float d = distance(hit_point, light_pos);
        if (d > 8.0) continue; // too far

        // Shadow DDA from hit_point toward light_pos
        vec2 ray_dir = normalize(light_pos - hit_point);
        // Nudge origin slightly along ray to avoid self-hit
        vec2 origin = hit_point + ray_dir * 0.001;

        ivec2 map_pos = ivec2(floor(origin));
        ivec2 step;
        vec2 delta_dist = abs(vec2(1.0) / ray_dir);
        vec2 side_dist;
        float max_dist = distance(origin, light_pos);

        // X setup
        if (ray_dir.x < 0.0) {
            step.x = -1;
            side_dist.x = (origin.x - float(map_pos.x)) * delta_dist.x;
        } else {
            step.x = 1;
            side_dist.x = (float(map_pos.x + 1) - origin.x) * delta_dist.x;
        }
        // Y setup
        if (ray_dir.y < 0.0) {
            step.y = -1;
            side_dist.y = (origin.y - float(map_pos.y)) * delta_dist.y;
        } else {
            step.y = 1;
            side_dist.y = (float(map_pos.y + 1) - origin.y) * delta_dist.y;
        }

        bool in_shadow = false;
        float current_dist = 0.0;
        // Limit steps to avoid infinite loops
        for (int si = 0; si < 64; si++) {
            if (side_dist.x < side_dist.y) {
                side_dist.x += delta_dist.x;
                map_pos.x += step.x;
                current_dist = side_dist.x - delta_dist.x;
            } else {
                side_dist.y += delta_dist.y;
                map_pos.y += step.y;
                current_dist = side_dist.y - delta_dist.y;
            }

            // If we've passed the light, nothing blocks it
            if (current_dist >= max_dist) {
                in_shadow = false;
                break;
            }

            // Sample map tile at current cell
            float tile = texture(u_map_tex, (vec2(map_pos) + 0.5) / u_map_size).r * 255.0;
            if (tile > 0.5) {
                in_shadow = true;
                break;
            }
        }

        if (!in_shadow) {
            total_light += brightness / (1.0 + d * d);
        }
    }
    return total_light;
}
// Parallax Occlusion Mapping with blob heightmap
vec2 parallax_blob(vec2 uv, vec2 view_dir) {
    float num_layers = 32.0;
    float layer_depth = 1.0 / num_layers;
    float current_depth = 0.0;
    
    // How much to shift UV per layer (based on view angle)
    vec2 delta_uv = view_dir.xy  / num_layers;  // 0.05 = depth scale
    
    vec2 current_uv = uv;
    
    for (float i = 0.0; i < 32.0; i++) {
        // Sample your blob as a heightmap (0 = flat, 1 = raised)
        vec2 buv = current_uv;
        mat2 m = rotate2D(5.0);
        vec2 n = vec2(0.0);
        float S = 12.0;
        float a = 0.0;
        for (float j = 0.0; j < 8.0; j++) {
            buv *= m;
            n *= m;
            vec2 q = buv * S + u_time * 0.3 + j + n;
            a += dot(cos(q) / S, vec2(0.2));
            n -= sin(q);
            S *= 1.2;
        }
        float height = a + 0.5;  // normalize to 0-1
        
        // Are we "below" the surface?
        if (current_depth >= height) break;

        current_uv -= delta_uv;
        current_depth += layer_depth;
    }
    return current_uv;
}

void main() {
    float column = gl_FragCoord.x;
    float half_fov = u_fov / 2.0;
    float delta_angle = u_fov / u_resolution.x;
    float ray_angle = u_player_angle - half_fov + column * delta_angle;
    vec2 ray_dir = vec2(cos(ray_angle), sin(ray_angle));
    float tile = 0.0;

    ivec2 map_pos = ivec2(floor(u_player_pos)); // which tile the player is in
    vec2 delta_dist = abs(vec2(1.0) / ray_dir); // how far to go in x/y to cross a tile boundary
    vec2 step_dir;
    vec2 side_dist;

    if (ray_dir.x < 0.0) {
        step_dir.x =-1.0;
        side_dist.x = (u_player_pos.x - float(map_pos.x)) * delta_dist.x;
    } else {
        step_dir.x = 1.0;
        side_dist.x = (float(map_pos.x + 1) - u_player_pos.x) * delta_dist.x;
    }
    if (ray_dir.y < 0.0) {
        step_dir.y = -1.0;
        side_dist.y = (u_player_pos.y - float(map_pos.y)) * delta_dist.y;
    } else {
        step_dir.y = 1.0;
        side_dist.y = (float(map_pos.y + 1) - u_player_pos.y) * delta_dist.y;
    }
    int hit_side = 0;
    for (int i = 0; i < 64; i++) {
        if (side_dist.x < side_dist.y) {
            side_dist.x += delta_dist.x;
            map_pos.x += int(step_dir.x);
            hit_side = 0;
        } else {
            side_dist.y += delta_dist.y;
            map_pos.y += int(step_dir.y);
            hit_side = 1;
        }

        vec2 tex_coord = (vec2(map_pos) + 0.5) / u_map_size;
        tile = texture(u_map_tex, tex_coord).r * 255.0;
        if (tile > 0.5) break;
    }
    
    float perp_dist;
    if (hit_side == 0) {
        perp_dist = (side_dist.x - delta_dist.x);
    } else {
        perp_dist = (side_dist.y - delta_dist.y);
    }

    float screen_dist = u_resolution.x / 2.0 / tan(u_fov / 2.0);
    float strip_height = screen_dist / max(perp_dist, 0.001);
    float center_y = u_resolution.y / 2.0 + u_bob_offset; // add head bobbing to vertical center
    float strip_top = center_y - strip_height / 2.0;
    float strip_bottom = center_y + strip_height / 2.0;
    float edge_noise = noise(vec2(float(map_pos.x + map_pos.y), column * 0.01) * 5.0) * 3.0;
    strip_top += edge_noise;
    strip_bottom -= edge_noise;
    float y = gl_FragCoord.y;

    if (y >= strip_top && y <= strip_bottom) {

        // UV coordinates
        float v = (y - strip_top) / strip_height;
        vec2 hit_point = u_player_pos + perp_dist * ray_dir;
        float u;
        if (hit_side == 0)
            u = fract(hit_point.y);
        else
            u = fract(hit_point.x);
        // Wall — shade by distance and side
        float shade = 1.0 / (1.0 + perp_dist * perp_dist * 0.04);
        float light = calc_lighting(hit_point);
        vec2 wall_uv = vec2(u, v);

        if (tile < 2.5 && tile > 1.5) {
            vec2 buv = wall_uv;
            mat2 m = rotate2D(5.0);
            vec2 n = vec2(0.0);
            float S = 12.0;
            float a = 0.0;
            for (float j = 0.0; j < 8.0; j++) {
                buv *= m;
                n *= m;
                vec2 q = buv * S + u_time + j + n;
                a += dot(cos(q) / S, vec2(0.2));
                n -= sin(q);
                S *= 1.2;
            }
            wall_uv += a;

            vec2 view_dir;
            if (hit_side == 0)
                view_dir = vec2(ray_dir.y, 1.0) * 0.5;  // looking along X wall
            else
                view_dir = vec2(ray_dir.x, 1.0) * 0.5;  // looking along Y wall
            wall_uv = parallax_blob(wall_uv, view_dir);
        }
        if (hit_side == 1) shade *= 0.7;
        vec3 wall_color;
        if (tile < 1.5)
            wall_color = brick_pattern(wall_uv);
        else if (tile < 2.5)
            wall_color = stone_pattern(wall_uv);
        else if (tile < 3.5)
            wall_color = metal_pattern(wall_uv);
        else
            wall_color = door_pattern(wall_uv);
        FragColor = vec4(wall_color * light * shade, 1.0);
        FragDepth = float(perp_dist);

    } else {
        float row_dist;
        vec3 floor_color;
        vec3 ceiling_color;

        if (y < strip_top) {
            // Floor (below wall in screen space)
            row_dist = (0.5 * screen_dist) / (center_y - y);
            vec2 world_pos = u_player_pos + row_dist * ray_dir;
            vec2 uv = fract(world_pos);

            vec2 buv = uv;
            mat2 m = rotate2D(5.0);
            vec2 n = vec2(0.0);
            float S = 12.0;
            float a = 0.0;
            for (float j = 0.0; j < 8.0; j++) {
                buv *= m;
                n *= m;
                vec2 q = buv * S + u_time + j + n;
                a += dot(cos(q) / S, vec2(0.2));
                n -= sin(q);
                S *= 1.2;
            }
            uv += a * 2.0;  // amplify floor noise

            float shade = 1.0 / (1.0 + row_dist * row_dist * 0.04);
            float light = calc_lighting(uv);
            floor_color = stone_pattern(uv);
            FragColor = vec4(floor_color * (light *4.0) * shade, 1.0);
            FragDepth = float(row_dist);
        } else {
            // Ceiling (above wall in screen space)
            row_dist = (0.5 * screen_dist) / (y - center_y);
            vec2 world_pos = u_player_pos + row_dist * ray_dir;
            vec2 uv = fract(world_pos);
            float shade = 1.0 / (1.0 + row_dist * row_dist * 0.04);
            float light = calc_lighting(uv);
            ceiling_color = metal_pattern(uv);
            FragColor = vec4(ceiling_color * light * shade, 1.0);
            FragDepth = float(row_dist);
        }
    }
    
}