package com.wendy.common.repository;

import java.time.Duration;
import java.util.Map;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Component
public class RedisSessionStore {
    private final StringRedisTemplate redis;
    private final long ttlSeconds = 3600;

    public RedisSessionStore(StringRedisTemplate redis){
        this.redis = redis;
    }

    private String key(String sesssionId){
        return "ws:session:" + sesssionId;
    }

    public void putSession(String sessionId, Map<String, String> meta){
        redis.opsForHash().putAll(key(sessionId), meta);
        redis.expire(key(sessionId), Duration.ofSeconds(ttlSeconds));
    }

    public Map<Object, Object> getSession(String sessionId) {
        return redis.opsForHash().entries(key(sessionId));
      }

    public void deleteSession(String sessionId) {
        redis.delete(key(sessionId));
    }

    public void touch(String sessionId) {
    redis.expire(key(sessionId), Duration.ofSeconds(ttlSeconds));
    }
}
