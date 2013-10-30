#!/usr/bin/python
#
"""
Holiday simulator with a PyGame display for local development.

Not as portable as the simpype in-browser display, but is more
responsive for things that need closer to hardware responsiveness.

Also allows you to simulate a multi-Holiday display by aggregating
the display of multiple Holiday instances if required.
"""

import optparse
import pygame
from holiday import HolidayRemote

class BaseOptParser(optparse.OptionParser):
    """
    Command-line options parser
    """
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        self.addOptions()

    def addOptions(self):
        self.add_option('-f', '--fps', dest='fps',
                        help="Frames per second, used to slow down simulator",
                        type="int")
        self.add_option('-n', '--numstrings', dest='numstrings',
                        help="Number of Holiday strings to simulate [%default]",
                        type="int", default=1)

        # Listen on multiple TCP/UDP ports, one for each Holiday we simulate
        self.add_option('-p', '--portstart', dest='portstart',
                        help="Port number to start at for UDP listeners [%default]",
                        type="int", default=9988)

        # Listener mode, TCP or UDP
        #self.add_option('-m', '--mode', dest='mode',
        #                help="Mode of the simulator, UDP or TCP [%default]",
        #                type="choice", choices=['udp', 'tcp'], default='udp')

        # Which way to draw multiple strings? Horizontally, like in the browser,
        # or vertically, like a string curtain?
        self.add_option('-o', '--orientation', dest='orientation',
                        help="Orientation of the strings [%default]",
                        type="choice", choices=['vertical', 'horizontal'], default='vertical')

        self.add_option('', '--spacing', dest='spacing',
                        help="Spacing between strings, in pixels. Overrides dynamic even spacing",
                        type="int")
        pass

    def parseOptions(self):
        """
        Emulate twistedmatrix options parser API
        """
        options, args = self.parse_args()
        self.options = options
        self.args = args

        self.postOptions()

        return self.options, self.args

    def postOptions(self):
        pass

class SimRunner(object):
    """
    A simulator for multiple Holidays

    Each Holiday listens on a local IP address, but each on its own port.
    """
    # Pixel width of gutters on each side of the screen
    gutter_width = 50

    # Size of each bulb
    bulb_diam = 10

    # Colour of the 'string' between the bulbs
    string_color = pygame.Color(255,255,255)

    # width of the 'string' line, in px
    string_width = 1

    # Number of bulbs per Holiday
    num_bulbs = 50

    # space to leave at each end of the string, in px
    string_header = 20
    string_footer = 10

    def __init__(self, options):
        self.options = options
        self.setup()

    def setup(self):

        self.numstrings = self.options.numstrings

        self.screen_x = 1024
        self.screen_y = 768
        
        self.HolidayList = [ ]
        for i in range(0, self.numstrings):
            self.HolidayList.append( HolidayRemote() )
            pass

        if not self.options.spacing:
            if self.numstrings > 1:
                if self.options.orientation == 'vertical':
                    self.spacer_width = ((self.screen_x - (2*self.gutter_width)) / self.numstrings) - self.bulb_diam
                elif self.options.orientation == 'horizontal':
                    self.spacer_width = ((self.screen_y - self.gutter_width) / self.numstrings) - self.bulb_diam
                    pass
                pass
            else:
                self.spacer_width = 0
                pass
            pass
        else:
            self.spacer_width = self.options.spacing
            pass
        print "spacer:", self.spacer_width
            
        pygame.init()
        # Default font to use
        self.fontsize = 24

        self.myFont = pygame.font.SysFont("None", self.fontsize)

        self.start_x = 0 + self.gutter_width
        self.start_y = (3 * self.myFont.get_height())
        
        # FIXME: Depends on orientation
        if self.options.orientation == 'vertical':
            self.string_length = self.screen_y - self.start_y - self.gutter_width
        elif self.options.orientation == 'horizontal':
            self.string_length = self.screen_x - self.start_x - 2*self.gutter_width

        pass
    
    def run(self):
        paused = False

        screen = pygame.display.set_mode([self.screen_x, self.screen_y])
        screen.fill((0,0,0))
        mainloop, x, y, color, delta, fps =  True, 25 , 0, (32,32,32), 1, 1000
        Clock = pygame.time.Clock()

        while mainloop:
            if self.options.fps:
                tickFPS = Clock.tick(self.options.fps)
                pass
            # Move the simulator forward one tick
            if not paused:
                pass

            pygame.display.set_caption("Press Esc or q to quit. p to pause. r to reset. FPS: %.2f" % (Clock.get_fps()))

            color = (255,255,255)

            # Black screen and update timer
            screen.fill((0,0,0))
            
            screen.blit(self.myFont.render("Holiday by MooresCloud Simulator", True, (color)), (x,y))
            screen.blit(self.myFont.render("(c) Justin Warren <justin@eigenmagic.com>", True, (color)), (x,y+self.myFont.get_height()))
            
            # Let the strings receive and process data
            self.recv_data()
            
            # Draw the Holiday strings
            self.draw_strings(screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    mainloop = False

                elif event.type == pygame.KEYDOWN:

                    # If quite key pressed, flag for exit
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        mainloop = False 

                    # Toggle pause
                    elif event.key == pygame.K_p:
                        if paused:
                            paused = False
                        else:
                            paused = True
                            pass
                        pass

                    # reset all strings to blank
                    elif event.key == pygame.K_r:
                        self.blank_strings()
                pass

            pygame.display.update()
            pass
        pygame.quit()
        pass

    def recv_data(self):
        """
        Process any data each simulated string may have received
        """
        for hol in self.HolidayList:
            hol.recv_udp()
            pass

    def blank_strings(self):
        """
        Reset all strings to black
        """
        for hol in self.HolidayList:
            hol.globes = [ (0x00, 0x00, 0x00) ] * hol.NUM_GLOBES
            pass
    
    def draw_strings(self, screen):
        """
        Draw the Holiday strings on the screen
        """
        # Figure out screen dimensions and place the strings accordingly

        for i, hol in enumerate(self.HolidayList):

            if self.options.orientation == 'vertical':
                xpos = self.start_x + (i*(self.bulb_diam + self.spacer_width))

                pygame.draw.line(screen, self.string_color,
                                 (xpos, self.start_y),
                                 (xpos, self.start_y + self.string_length),
                                 self.string_width)

                # Label the string with its number
                screen.blit(self.myFont.render("%d" % i, True, (255,255,255)),
                            (xpos - self.bulb_diam/2, self.start_y + self.string_length + self.bulb_diam))

                # Draw the lights
                for j in range(0, hol.NUM_GLOBES):
                    bulb_y = self.start_y + self.string_header + (
                        j * (self.string_length -
                             (self.string_header+self.string_footer)) / self.num_bulbs
                        )
                    # Fetch the globe color for globe j
                    r, g, b = hol.globes[j]
                    pygame.draw.circle(screen,
                                       pygame.Color(r, g, b),
                                       (xpos, bulb_y),
                                       self.bulb_diam / 2,
                                       )
                    pass
                pass

            elif self.options.orientation == 'horizontal':
                ypos = self.start_y + (i*(self.bulb_diam + self.spacer_width))
                
                pygame.draw.line(screen, self.string_color,
                                 (self.start_x, ypos),
                                 (self.start_x + self.string_length, ypos),
                                 self.string_width)
                            
                # Label the string with its number
                screen.blit(self.myFont.render("%d" % i, True, (255,255,255)),
                            (self.bulb_diam, ypos-self.bulb_diam))

                # Draw the lights
                for j in range(0, hol.NUM_GLOBES):
                    bulb_x = self.start_x + self.string_header + (
                        j * (self.string_length -
                             (self.string_header+self.string_footer)) / self.num_bulbs
                        )
                    # Fetch the globe color for globe j
                    r, g, b = hol.globes[j]
                    pygame.draw.circle(screen,
                                       pygame.Color(r, g, b),
                                       (bulb_x, ypos),
                                       self.bulb_diam / 2,
                                       )
                    pass
                pass
            pass
        pass
    pass

if __name__ == '__main__':
    optparse = BaseOptParser()
    options, args = optparse.parseOptions()

    sim = SimRunner(options)
    sim.run()
    
        
