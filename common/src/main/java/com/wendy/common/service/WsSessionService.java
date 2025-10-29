package com.wendy.common.service;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class WsSessionService {

    private final StringRedisTemplate redis;
    private final long ttlSeconds = 3600L; // session过期时间
    private final ObjectMapper objectMapper = new ObjectMapper();

    // 本地缓存：sessionId -> username
    private final Map<String, String> localCache = new ConcurrentHashMap<>();

    public WsSessionService(StringRedisTemplate redis) {
        this.redis = redis;
    }

    /** Redis Key 构建 */
    private String metaKey(String sessionId) {
        return "ws:session:meta:" + sessionId;
    }

    private String contextKey(String sessionId) {
        return "ws:session:context:" + sessionId;
    }

    /** 保存WebSocket会话元信息 */
    public void putSession(String sessionId, Map<String, String> meta) {
        redis.opsForHash().putAll(metaKey(sessionId), meta);
        redis.expire(metaKey(sessionId), Duration.ofSeconds(ttlSeconds));
        if (meta.containsKey("username")) {
            localCache.put(sessionId, meta.get("username"));
        }
        // 初始化上下文为空 Hash
        redis.opsForHash().putAll(contextKey(sessionId), Map.of());
        redis.expire(contextKey(sessionId), Duration.ofSeconds(ttlSeconds));
    }

    public void addContextPair(String sessionId, String question, String answer) {
        try {
            Map<String, Object> item = new HashMap<>();
            item.put("timestamp", System.currentTimeMillis());
            item.put("question", question);
            item.put("answer", answer);

            String json = objectMapper.writeValueAsString(item);
            redis.opsForList().rightPush(contextKey(sessionId), json);
            redis.expire(contextKey(sessionId), Duration.ofSeconds(ttlSeconds));
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize context pair", e);
        }
    }

    /** 获取session的元信息 */
    public Map<Object, Object> getSessionMeta(String sessionId) {
        return redis.opsForHash().entries(metaKey(sessionId));
    }

    public java.util.List<String> getContextList(String sessionId) {
        return redis.opsForList().range(contextKey(sessionId), 0, -1);
    }

    /** 批量更新上下文 */
    public void putContext(String sessionId, Map<String, Object> context) {
        redis.opsForHash().putAll(contextKey(sessionId), context);
        redis.expire(contextKey(sessionId), Duration.ofSeconds(ttlSeconds));
    }

    /** 删除session及上下文 */
    public void removeSession(String sessionId) {
        redis.delete(metaKey(sessionId));
        redis.delete(contextKey(sessionId));
        localCache.remove(sessionId);
    }

    /** 获取当前连接的用户名 */
    public String getUsername(String sessionId) {
        return localCache.get(sessionId);
    }

    /** 判断session是否存在 */
    public boolean exists(String sessionId) {
        return redis.hasKey(metaKey(sessionId));
    }
}