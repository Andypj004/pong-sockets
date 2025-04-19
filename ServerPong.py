import socket
import pickle
import pygame
import random
import sys
import time
from threading import Thread

class PongServer:
    def __init__(self, host='172.17.44.38', port=5000):
        self.host = host
        self.port = port
        
        # Configuracion del juego
        self.screen_width = 900
        self.screen_height = 600
        
        # Objetos del juego
        self.ball = pygame.Rect(self.screen_width/2 - 15, self.screen_height/2 - 15, 30, 30)
        self.player1 = pygame.Rect(self.screen_width - 20, self.screen_height/2 - 70, 10, 140)
        self.player2 = pygame.Rect(10, self.screen_height/2 - 70, 10, 140)
        
        # Variables del juego
        self.ball_speed_x = 7 * random.choice((1, -1))
        self.ball_speed_y = 7 * random.choice((1, -1))
        self.player1_score = 0
        self.player2_score = 0
        
        # Configuracion del servidor
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.socket.setblocking(False)  # Socket no bloqueante
        
        self.clients = [] # Lista de clientes conectados
        self.game_state = { # Estado actual del juego
            'ball': self.ball,
            'player1': self.player1,
            'player2': self.player2,
            'player1_score': self.player1_score,
            'player2_score': self.player2_score,
            'game_started': False,
            'countdown': 3,
            'winner': None
        }
        
        self.is_running = True # Control del bucle principal
        print(f"Server started on {self.host}:{self.port}")
    
    def ball_animation(self):
        self.ball.x += self.ball_speed_x
        self.ball.y += self.ball_speed_y
        
        # Colision en bordes superior e inferior
        if self.ball.top <= 0 or self.ball.bottom >= self.screen_height:
            self.ball_speed_y *= -1
            
        # Punto para jugador 1 (pelota sale por la izquierda)
        if self.ball.left <= 0:
            self.player1_score += 1
            self.ball_restart()
            if self.player1_score >= 5:
                self.game_state['winner'] = 1
            
        # Punto para jugador 2 (pelota sale por la derecha)
        if self.ball.right >= self.screen_width:
            self.player2_score += 1
            self.ball_restart()
            if self.player2_score >= 5:
                self.game_state['winner'] = 2
            
        # Colisiones con los jugadores
        if self.ball.colliderect(self.player1) and self.ball_speed_x > 0:
            if abs(self.ball.right - self.player1.left) < 10:
                self.ball_speed_x *= -1
            elif abs(self.ball.bottom - self.player1.top) < 10 and self.ball_speed_y > 0:
                self.ball_speed_y *= -1
            elif abs(self.ball.top - self.player1.bottom) < 10 and self.ball_speed_y < 0:
                self.ball_speed_y *= -1
                
        if self.ball.colliderect(self.player2) and self.ball_speed_x < 0:
            if abs(self.ball.left - self.player2.right) < 10:
                self.ball_speed_x *= -1
            elif abs(self.ball.bottom - self.player2.top) < 10 and self.ball_speed_y > 0:
                self.ball_speed_y *= -1
            elif abs(self.ball.top - self.player2.bottom) < 10 and self.ball_speed_y < 0:
                self.ball_speed_y *= -1
    
    def ball_restart(self):
        self.ball.center = (self.screen_width/2, self.screen_height/2)
        self.ball_speed_x = 0
        self.ball_speed_y = 0
        
        # Inicia cuenta regresiva
        self.game_state['countdown'] = 3
        self.game_state['game_started'] = False
        self.update_game_state() # Envia estado actualizado
        
        # Inicia cuenta regresiva en un hilo separado
        Thread(target=self.start_countdown).start()
    
    def start_countdown(self):
        for i in range(3, 0, -1): #Cuenta regresiva
            self.game_state['countdown'] = i
            self.update_game_state()
            time.sleep(1)
        
        # Inicia el juego después de la cuenta
        self.ball_speed_y = 7 * random.choice((1, -1))
        self.ball_speed_x = 7 * random.choice((1, -1))
        self.game_state['game_started'] = True
        self.update_game_state()
    
    def update_game_state(self):
        # Actualiza el estado del juego
        self.game_state['ball'] = self.ball
        self.game_state['player1'] = self.player1
        self.game_state['player2'] = self.player2
        self.game_state['player1_score'] = self.player1_score
        self.game_state['player2_score'] = self.player2_score
        
        # Envía el estado a todos los clientes
        for client in self.clients:
            try:
                self.socket.sendto(pickle.dumps(self.game_state), client)
            except:
                print(f"Error sending data to {client}")
    
    def process_client_data(self, data, client_address):
        try:
            data = pickle.loads(data) # Deserializa los datos
            client_id = data.get('client_id')
            action = data.get('action')
            
            # Conexión de nuevo cliente
            if action == 'connect':
                if client_address not in self.clients:
                    if len(self.clients) < 2: # Maximo dos jugadores
                        self.clients.append(client_address)
                        player_number = len(self.clients)
                        print(f"Player {player_number} connected from {client_address}")
                        
                        # Envía número de jugador al cliente
                        response = {'player_number': player_number}
                        self.socket.sendto(pickle.dumps(response), client_address)
                        
                        # Si hay 2 jugadores, inicia el juego
                        if len(self.clients) == 2:
                            print("Two players connected, starting countdown...")
                            Thread(target=self.start_countdown).start()
                    else:
                        # Servidor lleno
                        response = {'error': 'Server is full'}
                        self.socket.sendto(pickle.dumps(response), client_address)
            
            # Movimiento de jugador
            elif action == 'move':
                direction = data.get('direction')
                player_number = data.get('player_number')
                
                if player_number == 1:
                    if direction == 'up' and self.player1.top > 0:
                        self.player1.y -= 7
                    elif direction == 'down' and self.player1.bottom < self.screen_height:
                        self.player1.y += 7
                elif player_number == 2:
                    if direction == 'up' and self.player2.top > 0:
                        self.player2.y -= 7
                    elif direction == 'down' and self.player2.bottom < self.screen_height:
                        self.player2.y += 7
            
            # Desconexión de cliente
            elif action == 'disconnect':
                if client_address in self.clients:
                    self.clients.remove(client_address)
                    print(f"Client disconnected: {client_address}")
        
        except Exception as e:
            print(f"Error processing client data: {e}")
    
    def run(self):
        # Bucle del juego
        clock = pygame.time.Clock()
        last_update = time.time()
        
        while self.is_running:
            current_time = time.time()
            
            # Procesa los mensajes de los clientes
            try:
                while True:  # Procesar todos los mensajes disponibles
                    try:
                        data, client_address = self.socket.recvfrom(4096)
                        self.process_client_data(data, client_address)
                    except BlockingIOError:
                        # No mas mensajes
                        break
            except Exception as e:
                print(f"Error receiving data: {e}")
            
            # Actualizar la lógica del juego continuamente (independientemente del movimiento del jugador)
            if self.game_state['game_started']:
                self.ball_animation()
            
           # Mantener a los jugadores dentro de los límites de la pantalla
            if self.player1.top <= 0:
                self.player1.top = 0
            if self.player1.bottom >= self.screen_height:
                self.player1.bottom = self.screen_height
                
            if self.player2.top <= 0:
                self.player2.top = 0
            if self.player2.bottom >= self.screen_height:
                self.player2.bottom = self.screen_height
             
            # Enviar actualizaciones aproximadamente 60 veces por segundo
            if current_time - last_update >= 1/60:
                self.update_game_state()
                last_update = current_time
            
            clock.tick(60)

if __name__ == "__main__":
    server = PongServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server.socket.close()
        sys.exit()