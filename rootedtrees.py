""""
rootedtrees is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.
You should have received a copy of the GNU General Public License along
with planarforest. If not, see <http://www.gnu.org/licenses/>.

:Main author: Håkon Marthinsen
:Date: 2014-03-18
:Version: 4
:Contact: hakon.marthinsen@gmail.com

:Adaption author: Nicky Cordua Mattsson
:Date: 2015-12-18
:Version: 1
:Contact: nicky_mattsson@yahoo.dk
"""

# -*- coding: utf-8 -*-

class Node(object):
    """A node in a planar forest."""
    def __init__(self, children=None, color='b', x_pos=0.0,num='', parent=None):
        if children is None:
            children = []
        self.children = children
        self.color = color
        self.number = str(num)
        self.x_pos = x_pos
        self.parent = parent
        self.border_left = [0.0]
        self.border_right = [0.0]

    def __repr__(self):
        if len(self.children) == 0:
            return self.color
        else:
            string = self.color + "["
            for child in self.children:
                string += repr(child) + ","
            string = string[0:-1] + "]"
            return string

    def __str__(self):
        """Generate TikZ commands to draw the tree."""
        string = '\\node [' + self.color + ', label=right:'+ str(self.number) +'] at (' + str(self.x_pos) + \
            ', 0.0) {}\n'
        for child in self.children:
            string += child.tikz()
        string += ";\n"
        return string

    def tikz(self):
        """Returns TikZ commands for drawing this subtree. Internal usage."""
        string = 'child {node [' + str(self.color) + ', label=right:'+ str(self.number) +'] at (' + \
            str(self.x_pos - self.parent.x_pos) + ', 1.0) {}\n'
        for child in self.children:
            string += child.tikz()
        string += "}\n"
        return string

    def add_child(self, node):
        self.children.append(node)
        self.children[-1].parent = self

    def add_sibling(self, node):
        self.parent.add_child(node)

    def shift_x(self, offset):
        """
        Shift the whole subtree with self as root to the right by
        an amount equal to offset.
        """
        self.x_pos += offset
        self.border_left = [el + offset for el in self.border_left]
        self.border_right = [el + offset for el in self.border_right]
        for child in self.children:
            child.shift_x(offset)

    def optimize(self):
        """Arrange nodes of the tree optimally."""
        for child in self.children:
            child.optimize()

        if len(self.children) > 0:
            # Do nothing for leaves.

            # Arrange subtrees compactly.
            forest = Forest(self.children)
            forest.arrange_subtrees()
            self.border_left = forest.border_left[:]
            self.border_right = forest.border_right[:]

            # Place node at median of subtree root positions and convert to
            # relative coordinates.
            self.x_pos = median([child.x_pos for child in self.children])
            self.shift_x(-self.x_pos)

            self.border_left.insert(0, 0.0)
            self.border_right.insert(0, 0.0)


class Forest(object):
    def __init__(self, nodes=None):
        if nodes is None:
            nodes = []
        self.nodes = nodes
        self.border_left = []
        self.border_right = []

    def __str__(self):
        """Generate TikZ commands to draw the forest."""
        string = "\\tikz[planar forest] {\n"
        for subtree in self.nodes:
            string += str(subtree)
        string += "}"
        return string

    def append(self, node):
        self.nodes.append(node)

    def optimize(self):
        for subtree in self.nodes:
            subtree.optimize()
        self.arrange_subtrees()

    def arrange_subtrees(self):
        """Place optimal subtrees compactly."""
        # First scan from left to right.
        self.border_left = self.nodes[0].border_left[:]
        self.border_right = self.nodes[0].border_right[:]
        for subtree in self.nodes[1:]:
            for level in range(min(len(self.border_right),
                                   len(subtree.border_left))):
                delta = subtree.border_left[level] - self.border_right[level]
                if delta < 1:
                    subtree.shift_x(1.0 - delta)
            # Update borders
            self.border_left += subtree.border_left[len(self.border_left):]
            self.border_right = subtree.border_right + \
                self.border_right[len(subtree.border_right):]

        # Save the subtree positions for scan left to right and reset.
        pos_l_to_r = [subtree.x_pos for subtree in self.nodes]
        for subtree in self.nodes:
            subtree.shift_x(self.nodes[-1].x_pos - subtree.x_pos)

        # Next, scan from right to left while keeping the outer trees fixed.
        self.border_left = self.nodes[-1].border_left[:]
        self.border_right = self.nodes[-1].border_right[:]
        for subtree in reversed(self.nodes[:-1]):
            for level in range(min(len(self.border_left),
                                   len(subtree.border_right))):
                delta = self.border_left[level] - subtree.border_right[level]
                if delta < 1:
                    subtree.shift_x(delta - 1.0)
            # Update borders
            self.border_right += subtree.border_right[len(self.border_right):]
            self.border_left = subtree.border_left + \
                self.border_left[len(subtree.border_left):]

        # Save the subtree positions for scan right to left and reset middle
        # subtree positions.
        pos_r_to_l = [subtree.x_pos for subtree in self.nodes]
        for subtree in self.nodes[1:-1]:
            subtree.shift_x(self.nodes[0].x_pos - subtree.x_pos)

        # Place subtrees as close to evenly spaced out as possible.
        if len(self.nodes) > 1:
            optimal_dist = (pos_r_to_l[-1] -
                            pos_r_to_l[0]) / (len(self.nodes) - 1)
        for i in range(1, len(self.nodes) - 1):
            optimal_pos = i * optimal_dist + self.nodes[0].x_pos
            if optimal_pos < pos_l_to_r[i]:
                self.nodes[i].shift_x(pos_l_to_r[i] - self.nodes[i].x_pos)
            elif optimal_pos > pos_r_to_l[i]:
                self.nodes[i].shift_x(pos_r_to_l[i] - self.nodes[i].x_pos)
            else:
                self.nodes[i].shift_x(optimal_pos - self.nodes[i].x_pos)


def median(vector):
    """Calculate median of sorted vector."""
    length = len(vector)
    middle = length // 2
    if length % 2 == 1:
        return vector[middle]
    else:
        return 0.5 * (vector[middle] + vector[middle - 1])


def generate_forest(string):
    if len(string) == 0:
        return ""

    # Parse string and create forest.
    level = 0
    try:
        new_node = Node(color='b',num=str(int(string[0])))
    except ValueError:
        new_node = Node(color=string[0],num='')
    forest = Forest([new_node])
    current_node = new_node

    skip_next = False

    for i in range(1, len(string)):
        if skip_next:
            skip_next = False
            continue

        if string[i] == ",":
	    try:
	        new_node = Node(color='b',num=str(int(string[i + 1])))
	    except ValueError:
                new_node = Node(color=string[i + 1],num='')
            if level == 0:
                forest.append(new_node)
            else:
                current_node.add_sibling(new_node)
            current_node = new_node
            skip_next = True

        elif string[i] == "[":
            level += 1
            try: 
	        new_node = Node(color='b',num=str(int(string[i + 1])))
	    except ValueError:
                new_node = Node(color=string[i + 1],num="")
            current_node.add_child(new_node)
            current_node = new_node
            skip_next = True

        elif string[i] == "]":
            level -= 1
            current_node = current_node.parent

    # Place nodes.
    forest.optimize()

    # Generate TikZ code.
    return forest
