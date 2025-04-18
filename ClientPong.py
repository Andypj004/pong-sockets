import pygame
import socket
import pickle
import sys
import random
import uuid

class PongClient:
    def __init__(self, server_host='localhost', server_port=5000):
        # Inicializar Pygame
        pygame.init()
        self.clock = pygame.time.Clock()
        
        # Configuración de la ventana del juego
        self.screen_width = 900
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Pong Client')
        
        # Colores
        self.bg_color = pygame.Color('grey12')
        self.light_grey = (200, 200, 200)
        
        # texto
        self.game_font = pygame.font.Font("freesansbold.ttf", 32)
        
        # Configuración de red
        self.server_address = (server_host, server_port) # Dirección del servidor
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_id = str(uuid.uuid4())  # ID único para este cliente
        self.player_number = None # Número de jugador (1 o 2) asignado por el servidor
        
        # Estado inicial del juego (se actualizará desde el servidor)
        self.game_state = {
            'ball': pygame.Rect(self.screen_width/2 - 15, self.screen_height/2 - 15, 30, 30),
            'player1': pygame.Rect(self.screen_width - 20, self.screen_height/2 - 70, 10, 140),
            'player2': pygame.Rect(10, self.screen_height/2 - 70, 10, 140),
            'player1_score': 0,
            'player2_score': 0,
            'game_started': False,
            'countdown': 3
        }
        
        # Conectar al servidor
        self.connect_to_server()
    
    def connect_to_server(self):
        try:
            # Configurar socket como no bloqueante
            self.socket.setblocking(0)
            
            # Enviar solicitud de conexión
            data = {
                'client_id': self.client_id,
                'action': 'connect'
            }
            self.socket.sendto(pickle.dumps(data), self.server_address)
            
            print(f"Connection request sent to {self.server_address}")
            
            # Esperar respuesta
            waiting_for_response = True
            start_time = pygame.time.get_ticks()
            
            while waiting_for_response:
                current_time = pygame.time.get_ticks()
                
                # Timeout después de 5 segundos
                if current_time - start_time > 5000:
                    print("Connection timeout")
                    sys.exit()
                
                # Verificar eventos (para no bloquear la interfaz)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                
                # Intentar recibir respuesta
                try:
                    data, _ = self.socket.recvfrom(4096)
                    response = pickle.loads(data)
                    
                    if 'player_number' in response:
                        self.player_number = response['player_number']
                        waiting_for_response = False
                        print(f"Connected as Player {self.player_number}")
                        
                        # Mostrar mensaje de espera si es jugador 1
                        if self.player_number == 1:
                            self.display_waiting_screen()
                    
                    elif 'error' in response:
                        print(f"Error: {response['error']}")
                        pygame.quit()
                        sys.exit()
                        
                except:
                    # No se recibieron datos, continuar esperando
                    pass
                
                pygame.time.delay(100)
                
        except Exception as e:
            print(f"Connection error: {e}")
            pygame.quit()
            sys.exit()
    
    def display_waiting_screen(self):
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.disconnect()
                    pygame.quit()
                    sys.exit()
            
            # Intentar recibir estado del juego
            try:
                data, _ = self.socket.recvfrom(4096)
                game_state = pickle.loads(data)
                
                # Si recibimos estado con 2 jugadores, dejar de esperar
                if len(game_state) > 0:
                    self.game_state = game_state
                    if 'countdown' in self.game_state and self.game_state['countdown'] <= 3:
                        waiting = False
            except:
                pass
            
            # Dibujar pantalla de espera
            self.screen.fill(self.bg_color)
            waiting_text = self.game_font.render("Waiting for Player 2...", True, self.light_grey)
            self.screen.blit(waiting_text, (self.screen_width//2 - 150, self.screen_height//2))
            pygame.display.flip()
            self.clock.tick(60)
    
    def send_movement(self, direction):
        try:
            # Prepara los datos del movimiento en un diccionario
            data = {
                'client_id': self.client_id,
                'action': 'move',
                'direction': direction,
                'player_number': self.player_number
            }
            # Serializa los datos y los envía al servidor via UDP
            self.socket.sendto(pickle.dumps(data), self.server_address)
        except Exception as e:
            print(f"Error sending movement: {e}")
    
    def disconnect(self):
        try:
            # Prepara los datos de desconexión
            data = {
                'client_id': self.client_id,
                'action': 'disconnect'
            }
            # Envía la notificación al servidor
            self.socket.sendto(pickle.dumps(data), self.server_address)
        except:
            pass
    
    def receive_game_state(self):
        try:
             # Recibe datos del servidor
            data, _ = self.socket.recvfrom(4096)
            # Deserializa los datos y actualiza el estado del juego
            self.game_state = pickle.loads(data)
        except:
            pass
    
    def draw_game(self):
        # Fondo
        self.screen.fill(self.bg_color)
        
        # Linea Central
        pygame.draw.aaline(self.screen, self.light_grey, (self.screen_width/2, 0), (self.screen_width/2, self.screen_height))
        
        # Jugadores
        pygame.draw.rect(self.screen, self.light_grey, self.game_state['player1'])
        pygame.draw.rect(self.screen, self.light_grey, self.game_state['player2'])
        
        # Pelota
        pygame.draw.ellipse(self.screen, self.light_grey, self.game_state['ball'])
        
        # Marcador
        player1_text = self.game_font.render(f"{self.game_state['player1_score']}", False, self.light_grey)
        self.screen.blit(player1_text, (480, 290))
        player2_text = self.game_font.render(f"{self.game_state['player2_score']}", False, self.light_grey)
        self.screen.blit(player2_text, (400, 290))
        
        # Cuenta regresiva si el juego no ha comenzado
        if not self.game_state['game_started'] and 'countdown' in self.game_state:
            countdown_text = self.game_font.render(f"{self.game_state['countdown']}", False, self.light_grey)
            self.screen.blit(countdown_text, (self.screen_width/2 - 10, self.screen_height/2 + 70))
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Controles del jugador
            keys = pygame.key.get_pressed()
            
            # Jugador 1 usa flechas
            if self.player_number == 1:
                if keys[pygame.K_UP]:
                    self.send_movement('up')
                if keys[pygame.K_DOWN]:
                    self.send_movement('down')
            
            # Jugador 2 usa W y S
            elif self.player_number == 2:
                if keys[pygame.K_w]:
                    self.send_movement('up')
                if keys[pygame.K_s]:
                    self.send_movement('down')
            
            # Recibir estado actualizado del juego
            self.receive_game_state()
            
            self.draw_game()
            
            # Actualizar pantalla
            pygame.display.flip()
            self.clock.tick(60)
        
        # Desconexión del servidor
        self.disconnect()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    host = 'localhost' 
    port = 5000  
    
    # Manejo de argumentos de línea de comandos
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    client = PongClient(host, port)
    client.run()