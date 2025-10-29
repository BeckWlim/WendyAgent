package com.wendy.common.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.*;

import com.wendy.common.handler.WsHandler;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final WsHandler wsHandler;

    public WebSocketConfig(WsHandler wsHandler) {
        this.wsHandler = wsHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(wsHandler, "/ws/chat")
            .addInterceptors(new WsHandshakeInterceptor())
            .setAllowedOrigins("*");
    }
}
