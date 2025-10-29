package com.wendy.auth.service;

import java.security.InvalidKeyException;
import java.util.Date;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.wendy.auth.repository.TokenRepository;
import com.wendy.auth.repository.UserRepository;
import com.wendy.auth.utils.JwtUtil;
import com.wendy.auth.dto.*;
import com.wendy.auth.entity.User;
import com.wendy.auth.exception.CustomAuthException;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;
    private final TokenRepository redisTokenRepository;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            AuthenticationManager authenticationManager,
            JwtUtil jwtUtil,
            TokenRepository redisTokenRepository
    ) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.authenticationManager = authenticationManager;
        this.jwtUtil = jwtUtil;
        this.redisTokenRepository = redisTokenRepository;
    }

    // 用户注册
    @Transactional
    public void register(UserRegistrationDto dto) {
        // 校验用户名/邮箱是否已存在
        if (userRepository.existsByUsername(dto.getUsername())) {
            throw new RuntimeException("Username already exists");
        }
        if (userRepository.existsByEmail(dto.getEmail())) {
            throw new RuntimeException("Email already exists");
        }

        // 创建用户并加密密码
        User user = new User();
        user.setUsername(dto.getUsername());
        user.setPassword(passwordEncoder.encode(dto.getPassword()));  // BCrypt加密
        user.setEmail(dto.getEmail());
        userRepository.save(user);
    }

    // 用户登录（返回令牌）
    public AuthResponse login(UserLoginDto dto) {
        // 认证用户名密码
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(dto.getUsername(), dto.getPassword())
        );

        // 生成令牌
        String username = authentication.getName();
        String accessToken = jwtUtil.generateAccessToken(username);
        String refreshToken = jwtUtil.generateRefreshToken(username);

        return new AuthResponse(accessToken, refreshToken);
    }

    // 用户注销（将令牌加入Redis黑名单）
    public void logout(String token) {
        // 验证令牌有效性
        if (jwtUtil.isTokenExpired(token)) {
            throw new RuntimeException("Token already expired");
        }
        // 计算剩余过期时间，作为黑名单缓存时间
        long remainingTime = jwtUtil.extractExpiration(token).getTime() - new Date().getTime();
        redisTokenRepository.addToBlacklist(token, remainingTime);
    }

    // 刷新令牌
    public AuthResponse refreshToken(String refreshToken) {
        String username = jwtUtil.extractUsername(refreshToken);
        if (!jwtUtil.validateToken(refreshToken, username)) {
            throw new RuntimeException("Invalid refresh token");
        }
        return new AuthResponse(
            jwtUtil.generateAccessToken(username),
            jwtUtil.generateRefreshToken(username)
        );
    }

    public void verifyToken(String token, String username){
        try{
            Boolean isValid = jwtUtil.validateToken(token, username);
            if (!isValid){
                throw new InvalidKeyException("Token is invalid");
            }
        } catch (Exception e){
            throw new CustomAuthException("Token is invalid or expired");
        }
    }
}