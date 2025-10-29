package com.wendy.auth.repository;

import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;
import java.util.concurrent.TimeUnit;

@Repository
public class TokenRepository {
    private final RedisTemplate<Object, Object> redisTemplate;
    private static final String BLACKLIST_PREFIX = "token:blacklist:";

    public TokenRepository(RedisTemplate<Object, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    // 将令牌加入黑名单（注销时使用）
    public void addToBlacklist(String token, long expirationMillis) {
        String key = BLACKLIST_PREFIX + token;
        redisTemplate.opsForValue().set(key, "blacklisted", expirationMillis, TimeUnit.MILLISECONDS);
    }

    // 检查令牌是否在黑名单中
    public boolean isBlacklisted(String token) {
        String key = BLACKLIST_PREFIX + token;
        return redisTemplate.hasKey(key);
    }
}