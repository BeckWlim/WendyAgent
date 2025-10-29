package com.wendy.common.service;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class RabbitMqService {
    private final RabbitTemplate rabbitTemplate;
    private final String agentQueue = "agent.request.queue";
    private final String agentResponseQueue = "agent.response.queue";
    private Logger logger = LoggerFactory.getLogger(RabbitMqService.class);

    private final Map<String, CompletableFuture<String>> pendingResponses = new ConcurrentHashMap<>();

    public RabbitMqService(RabbitTemplate template){
        this.rabbitTemplate = template;
    }

    public CompletableFuture<String> sendMessageToAgent(Map<String, Object> message) throws JsonProcessingException{
        String correlationId = UUID.randomUUID().toString();
        message.put("correlationId", correlationId);
        CompletableFuture<String> future = new CompletableFuture<>();

        ObjectMapper mapper = new ObjectMapper();
        try {
            String jsonStr = mapper.writeValueAsString(message);
            pendingResponses.put(correlationId, future);
            rabbitTemplate.convertAndSend(agentQueue, jsonStr);
        } catch (JsonProcessingException e) {
            throw e;
        }
        return future;
    }

    @RabbitListener(queues = agentResponseQueue)
    public void onAgentResponse(String messageBody) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> message = mapper.readValue(messageBody, Map.class);

            String correlationId = (String) message.get("correlationId");
            String reply = (String) message.get("reply");

            CompletableFuture<String> future = pendingResponses.remove(correlationId);
            if (future != null) {
                future.complete(reply);
            }
        } catch (Exception e) {
            logger.error("Failed to process message: {}", messageBody, e);
        }
    }
}
