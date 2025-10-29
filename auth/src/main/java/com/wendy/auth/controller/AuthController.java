package com.wendy.auth.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.wendy.auth.dto.*;
import com.wendy.auth.service.AuthService;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    // 注册接口
    @PostMapping("/register")
    public ResponseEntity<String> register(@RequestBody UserRegistrationDto dto) {
        authService.register(dto);
        return ResponseEntity.ok("User registered successfully");
    }

    // 登录接口
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody UserLoginDto dto) {
        AuthResponse response = authService.login(dto);
        return ResponseEntity.ok(response);
    }

    // 注销接口（需要携带令牌）
    @PostMapping("/logout")
    public ResponseEntity<String> logout(@RequestHeader("Authorization") String token) {
        // 去除Bearer前缀
        String jwtToken = token.replace("Bearer ", "");
        authService.logout(jwtToken);
        return ResponseEntity.ok("Logged out successfully");
    }

    // 刷新令牌接口
    @PostMapping("/refresh")
    public ResponseEntity<AuthResponse> refreshToken(@RequestBody RefreshTokenDto dto) {
        AuthResponse response = authService.refreshToken(dto.getRefreshToken());
        return ResponseEntity.ok(response);
    }

    // 验证调用
    @PostMapping("/verify")
    public ResponseEntity<Void> verify(
        @RequestHeader("Authorization") String token,
        @RequestParam("username") String username){

        String jwtToken = token.replace("Bearer ", "");
        authService.verifyToken(jwtToken, username);
        return ResponseEntity.ok().build();
    }
}
