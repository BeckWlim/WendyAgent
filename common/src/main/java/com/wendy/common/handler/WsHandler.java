package com.wendy.common.handler;

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
        // 从query参数或header中获取token
        String username = (String) session.getAttributes().get("username");
        logger.debug("User: {}, Id: {}", username, session.getId());
        // 假设：token已经由gateway/auth验证过
        Map<String, String> meta = new HashMap<>();
        meta.put("username", username);

        wsSessionService.putSession(session.getId(), meta);
        session.sendMessage(new TextMessage("Connected as " + username));
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
                    wsSessionService.addContextPair(sessionId, payload, answer);
                    session.sendMessage(new TextMessage(answer));
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
