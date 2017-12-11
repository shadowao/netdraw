# -*- coding: utf-8 -*-


import networkx as nx
import Tkinter as tk
from tkFileDialog import askopenfile


class GraphCanvas(tk.Canvas):
    """ Main Structure For Draw Networkx"""

    def __init__(self, graph, *args, **kwargs):
        """ You Must Convert A Networkx Graph"""
        self.graph = graph

        # The position of every node
        self.pos = None

        # We use a canvas item to draw node and edge, so every node map to a node_items, and
        # every edge has a edge_item, too.
        # The key is the item id created by canvas, not the networkx graph node id or edge id
        self.node_items = {}
        self.edge_items = {}

        # This is the canvas item, you can customize it. but you need to implements some interface
        self.NodeItemClass = kwargs.pop('NodeItemClass', NodeItem)
        self.EdgeItemClass = kwargs.pop('EdgeItemClass', EdgeItem)

        # The canvas's init size
        self.width = kwargs.pop('width', 500)
        self.height = kwargs.pop('height', 500)

        tk.Canvas.__init__(self, width=self.width, height=self.height, *args, **kwargs)

        # This is used to drag node or the whole canves, see onLeftButtonPress, onLeftButtonRelease, onLeftButtonMotion
        self.drag_event = None
        self.bind('<ButtonPress-1>', self.onLeftButtonPress)
        self.bind('<ButtonRelease-1>', self.onLeftButtonRelease)
        self.bind('<B1-Motion>', self.onLeftButtonMotion)

        # This for mark a item (node or edge when click)
        self.bind('<ButtonPress-3>', self.onRightButtonPress)

        # Zoom canvas
        self.bind_all('<MouseWheel>', self.onZoom)

        # draw action
        self.draw()

    def draw(self):
        """ We draw nodes first, then edges"""
        graph = self.graph

        for node in graph.nodes():
            self.draw_node(node)
        for edge in graph.edges():
            self.draw_edge(edge)

        # We need to put the node on the canvas's stack top, if not, we will see the line in node
        for item in self.find_withtag('Edge'):
            self.tag_lower(item)

    def draw_node(self, node):
        """Draw a node item on the canvas,
           we get the pos of node, first, if there is no pos, we will use spring_layout to init the pos
           Then create Node Item Class, you should transfer the config to constrctor
           Next to draw it on the canvas
           Last, we need store it on the node items for use later
        """
        pos = self.get_node_pos(node)
        item = self.NodeItemClass(self, node, pos, tags='Node')
        item_id = item.draw()

        # store infomation for later
        self.graph.nodes[node]['item_id'] = item_id
        self.node_items[item_id] = item

    def draw_edge(self, edge):
        """Same as Node"""
        pos = self.get_edge_pos(edge)
        item = self.EdgeItemClass(self, edge, self.graph.edges[edge], pos, tags='Edge')
        item_id = item.draw()

        self.graph.edges[edge]['item_id'] = item_id
        self.edge_items[item_id] = item

    def get_node_pos(self, node):
        if self.pos is None:
            self.calc_pos()
        return self.pos[node]

    def get_edge_pos(self, edge):
        """ Return the potion of node of the edge"""
        if self.pos is None:
            self.calc_pos()
        u, v = edge
        return list(self.get_node_pos(u)) + list(self.get_node_pos(v))

    def calc_pos(self):
        """ If there is no pos, we use networkx spring layout to init the pos,
            Or, we get the position by canvas.coords method for every node
        """
        if self.pos is None:
            width = self.width
            height = self.height

            center_x, center_y = width/2.0, height/2.0
            scale = min(center_x, center_y)

            self.pos = nx.spring_layout(self.graph, scale=scale, center=(center_x, center_y))
        else:
            for node_item_id, node_item in self.node_items.items():
                x0, y0, x1, y1 = self.bbox(node_item_id)
                self.pos[node_item.node] = (x0 + x1)/2.0, (y0 + y1)/2.0
        return self.pos

    def get_node_overlapping(self, event):
        item_ids = self.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        for item_id in item_ids:
            if 'Node' in self.gettags(item_id):
                return item_id
        return None

    def get_edge_overlapping(self, event):
        item_ids = self.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        for item_id in item_ids:
            if 'Edge' in self.gettags(item_id):
                return item_id
        return None

    def move_node(self, start_x, start_y, end_x, end_y, item_id):
        """Move Node and Edge Assostioned"""
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        self.node_items[item_id].move(delta_x, delta_y)

        node = self.node_items[item_id].node
        x0, y0 = end_x, end_y
        self.pos[node] = end_x, end_y
        for other, attr in self.graph.adj[node].items():
            x1, y1 = self.pos[other]
            self.edge_items[attr['item_id']].move(x0, y0, x1, y1)

    def move_all(self, start_x, start_y, end_x, end_y):
        delta_x = end_x - start_x
        delta_y = end_y - start_y

        self.move(tk.ALL, delta_x, delta_y)

        self.calc_pos()

    def onLeftButtonPress(self, event):
        item_id = self.get_node_overlapping(event)

        if item_id is None:
            self.drag_event = {'start_x': event.x, 'start_y': event.y, 'is_node': False}
        else:
            self.drag_event = {'start_x': event.x, 'start_y': event.y, 'is_node': True, 'item_id': item_id}

    def onLeftButtonRelease(self, event):
        self.drag_event = None

    def onLeftButtonMotion(self, event):
        start_x, start_y = self.drag_event['start_x'], self.drag_event['start_y']

        end_x, end_y = event.x, event.y

        if self.drag_event['is_node']:
            self.move_node(start_x, start_y, end_x, end_y, self.drag_event['item_id'])
        else:
            self.move_all(start_x, start_y, end_x, end_y)

        self.drag_event['start_x'], self.drag_event['start_y'] = end_x, end_y

    def onZoom(self, event):
        factor = 0.1 if event.delta > 0 else -0.1

        center_x, center_y = float(self['width'])/2.0, float(self['height'])/2.0

        for node_item_id, node_item in self.node_items.items():
            x, y = self.pos[node_item.node]

            dx = abs(center_x - x) * factor
            dy = abs(center_y - y) * factor

            self.pos[node_item.node] = x + dx, y + dy
            self.node_items[node_item_id].move(dx, dy)

        for u, v, d in self.graph.edges(data=True):
            x0, y0 = self.pos[u]
            x1, y1 = self.pos[v]
            self.edge_items[d['item_id']].move(x0, y0, x1, y1)


    def onRightButtonPress(self, event):
        """When you press the right button, the node will be marked if you click on the node,
           or the line if click on the line, otherwise nothing.
        """

        item_id = self.get_node_overlapping(event)
        if item_id:
            self.node_items[item_id].mark()
        else:
            item_id = self.get_edge_overlapping(event)
            if item_id:
                self.edge_items[item_id].mark()


class NodeItem(object):

    def __init__(self, canvas, node, pos, tags, *args, **kwargs):
        self.width = kwargs.pop('width', 10)
        self.height = kwargs.pop('height', 10)

        self.canvas = canvas
        self.node = node
        self.pos = pos
        self.tags = tags
        self.id = None
        self.text_id = None

    def draw(self):
        canvas = self.canvas
        x, y = self.pos
        width, height = self.width/2.0, self.height/2.0
        self.id = canvas.create_oval(x - width, y - height, x + width, y + height, fill='blue', tags=self.tags)

        self.text_id = canvas.create_text(x + width*1.5, y + height*1.5, text=self.node, anchor=tk.CENTER)
        return self.id

    def move(self, dx, dy):
        self.canvas.move(self.id, dx, dy)
        self.canvas.move(self.text_id, dx, dy)

    def get_pos(self):
        x0, y0, x1, y1 = self.canvas.bbox(self.id)
        return (x0 + x1)/2.0, (y0 + y1)/2.0

    def mark(self):
        self.canvas.itemconfig(self.id, fill='red')

    def unmark(self):
        self.canvas.itemconfig(self.id, fill='blue')


class EdgeItem(object):

    def __init__(self, canvas, edge, edge_attr, pos, tags, *args, **kwargs):
        self.canvas = canvas
        self.pos = pos
        self.tags = tags
        self.edge = edge
        self.edge_attr = edge_attr
        self.id = None
        self.text_id = None

    def draw(self):
        self.id = self.canvas.create_line(*self.pos, tags=self.tags)
        self.text_id = self.canvas.create_text((self.pos[0] + self.pos[2])/2.0,
                                               (self.pos[1] + self.pos[3])/2.0,
                                               text=self.edge_attr.get('weight', 1), anchor=tk.CENTER)
        return self.id

    def move(self, x0, y0, x1, y1):
        self.canvas.coords(self.id, x0, y0, x1, y1)
        self.canvas.coords(self.text_id, (x0 + x1)/2.0, (y0 + y1)/2.0)

    def get_pos(self):
        return self.bbox(self.id)

    def mark(self):
        self.canvas.itemconfig(self.id, fill='red')

    def unmark(self):
        self.canvas.itemconfig(self.id, fill='black')


class Viewer(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.geometry(str(self.winfo_screenwidth()/2) + 'x' + str(self.winfo_screenheight()/2))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label='Open', command=self.open_file)
        self.menu_bar.add_cascade(label='File', menu=file_menu)

        graph_menu = tk.Menu(self.menu_bar, tearoff=0)
        graph_menu.add_command(label='Star', command=lambda: self.draw_graph(nx.star_graph(20)))
        graph_menu.add_command(label='Path', command=lambda: self.draw_graph(nx.path_graph(10)))
        graph_menu.add_command(label='Random', command=lambda: self.draw_graph(nx.random_geometric_graph(20, 0.25)))
        graph_menu.add_command(label='Cubical', command=lambda: self.draw_graph(nx.cubical_graph()))
        graph_menu.add_command(label='Gnm Random', command=lambda: self.draw_graph(nx.gnm_random_graph(10, 20)))
        self.menu_bar.add_cascade(label='Graph', menu=graph_menu)

    def draw_graph(self, graph):
        graph_canvas = GraphCanvas(graph, master=self, width=self.winfo_screenwidth()/2, height=self.winfo_screenheight()/2)
        graph_canvas.grid(row=0, column=0, sticky='NESW')

    def open_file(self):
        file_path = askopenfile()
        self.draw_graph(nx.read_edgelist(file_path))


if __name__ == '__main__':
    app = Viewer()
    app.mainloop()
