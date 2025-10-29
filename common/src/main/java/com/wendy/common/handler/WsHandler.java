package com.wendy.common.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wendy.common.service.RabbitMqService;
import com.wendy.common.service.WsSessionService;
import jakarta.annotation.Resource;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@Component
public class WsHandler extends TextWebSocketHandler {
    private static final Logger logger = LoggerFactory.getLogger(WsHandler.class);
    @Resource
    private WsSessionService wsSessionService;
    @Resource
    private RabbitMqService rabbitMqService;

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        // 从query header中获取token
        String username = (String) session.getAttributes().get("username");
        String sessionId = session.getId();
        logger.debug("User: {}, Id: {}", username, sessionId);

        Map<String, String> meta = new HashMap<>();
        meta.put("username", username);
        meta.put("sessionId", sessionId);
        wsSessionService.putSession(sessionId, meta);

        Map<String, String> payload = new HashMap<>();
        payload.put("type", "session_init");
        payload.put("sessionId", sessionId);
        payload.put("username", username);

        String json = new ObjectMapper().writeValueAsString(payload);
        session.sendMessage(new TextMessage(json));
    }

    @Override
    public void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String username = wsSessionService.getUsername(session.getId());
        String payload = message.getPayload();
        String sessionId = session.getId();

        logger.debug("Received message from {}: {}", username, payload);

        Map<String, Object> rabbit_message = new HashMap<>();
        rabbit_message.put("question", payload);
        rabbit_message.put("history", wsSessionService.getContextList(sessionId));
        rabbit_message.put("meta", wsSessionService.getSessionMeta(sessionId));

        CompletableFuture<String> future = rabbitMqService.sendMessageToAgent(rabbit_message);

        future.thenAccept(answer -> {
            try {
                if (session.isOpen()) {
                    Map<String, Object> resp = new HashMap<>();
                    resp.put("type", "response");
                    resp.put("answer", answer);

                    String json = new ObjectMapper().writeValueAsString(resp);
                    wsSessionService.addContextPair(sessionId, payload, answer);
                    session.sendMessage(new TextMessage(json));
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        wsSessionService.removeSession(session.getId());
    }
}
