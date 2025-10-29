package com.wendy.auth.utils;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.function.Function;
import javax.crypto.SecretKey;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class JwtUtil {
    @Value("${jwt.secret}")
    private String secretKey;

    @Value("${jwt.expiration}")
    private long accessTokenExpiration;

    @Value("${jwt.refresh-token.expiration}")
    private long refreshTokenExpiration;
    private static final Logger logger = LoggerFactory.getLogger(JwtUtil.class);

    // 初始化：对密钥进行Base64编码（JJWT要求）
    @PostConstruct
    protected void init() {
        secretKey = java.util.Base64.getEncoder().encodeToString(secretKey.getBytes(StandardCharsets.UTF_8));
    }

    // 生成访问令牌
    public String generateAccessToken(String username) {
        return generateToken(username, accessTokenExpiration);
    }

    // 生成刷新令牌
    public String generateRefreshToken(String username) {
        return generateToken(username, refreshTokenExpiration);
    }

    private String generateToken(String username, long expiration) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expiration);

        SecretKey key = Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));

        return Jwts.builder()
                .setSubject(username)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    // 从令牌中获取用户名
    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    // 验证令牌是否有效（未过期、签名正确、用户名匹配）
    public boolean validateToken(String token, String username) {
        logger.debug("validateToken method used，user [{}], token: [{}]",
                username,
                token != null ? token.substring(0, Math.min(10, token.length())) : "null");
        try {
            final String extractedUsername = extractUsername(token);
            return (extractedUsername.equals(username) && !isTokenExpired(token));
        } catch (JwtException | IllegalArgumentException e) {
            logger.debug("validate fail");
            return false;
        }
    }

    // 检查令牌是否过期
    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    private <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    private Claims extractAllClaims(String token) {
        SecretKey key = Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));
        // 2. 使用新的 parserBuilder() 构建解析器
        return Jwts.parserBuilder()
                .setSigningKey(key)  // 设置签名密钥（使用 SecretKey 类型）
                .build()  // 构建解析器
                .parseClaimsJws(token)  // 解析令牌
                .getBody();  // 获取声明（Claims）
    }
}
