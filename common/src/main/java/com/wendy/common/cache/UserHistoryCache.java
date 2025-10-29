package com.wendy.common.cache;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class UserHistoryCache {

    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper;

    public UserHistoryCache(RedisTemplate<String, String> redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    private String getKey(String userId) {
        return "user:" + userId + ":history";
    }

    public void addMessage(String userId, Object message) throws Exception {
        String json = objectMapper.writeValueAsString(message);
        redisTemplate.opsForList().leftPush(getKey(userId), json);
        redisTemplate.opsForList().trim(getKey(userId), 0, 9);
    }

    public <T> List<T> getHistory(String userId, Class<T> clazz) {
        List<String> list = redisTemplate.opsForList().range(getKey(userId), 0, 9);
        if (list == null) return List.of();
        return list.stream().map(s -> {
            try {
                return objectMapper.readValue(s, clazz);
            } catch (Exception e) {
                return null;
            }
        }).collect(Collectors.toList());
    }
}
