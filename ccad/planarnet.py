import networkx as nx
import matplotlib.pyplot as plt
import ccad.model as cm
import ccad.display as cd
import numpy as np
import pdb

class PlanarNet(nx.Graph):
    def __init__(self,**kwargs):
        """
        Parameters
        ----------
        pt : np.array (N x 2)
            points in the 0xy plane
        N : number of nodes of the first polygon
        l : edge length of the first polygon

        """
        self.folded = False
        pt = kwargs.pop('pt',[])
        N  = kwargs.pop('N',3)
        self.l  = kwargs.pop('l',1)
        if pt==[]:
            al = (N-2)*np.pi/(2*N)
            self.r = np.sin(al)/np.sin(2*np.pi/N)
            self.s = np.sqrt(self.r**2-self.l**2/4.)
            t = np.linspace(0,N,N+1)
            u = 2*np.pi*t/N
            pt = self.r * np.c_[np.cos(u),np.sin(u)]
        N = pt.shape[0]
        # conversion to 3D
        self.pt = np.c_[pt[:,0],pt[:,1],np.zeros(N)]
        w0 = cm.polygon(self.pt)
        face0 = cm.plane(w0)
        self.lfaces = [face0]
        self.nnode = 0
        nx.Graph.__init__(self)
        self.add_node(0)
        self.pos = {}
        self.pos[0] = face0.center()[0:2]

    def __repr__(self):
        st = 'PlanarNet :'+str(self.nnode + 1) + '\n'
        if self.folded:
            st = st +'Folded\n'
        for f in self.lfaces:
            st = st + f.__repr__()
        return st

    def __add__(self,other):
        new = PlanarNet()
        new.lfaces = self.lfaces + other.lfaces
        new.shell = cm.Shell(new.lfaces)
        return new

    def __copy__(self):
        return(self)

    def translated(self,pdir):
        """
        """
        pass

    def rotated(self,pabout,angle):
        pass


    def plot(self):
        for f in self.lfaces:
            f.plot()
            for k,e in enumerate(f.subshapes('Edge')):
                eps = self.l/15.
                xe , ye = e.center()[0:2]
                lv = e.subshapes('Vertex')
                p0 = np.array(lv[0].center())
                p1 = np.array(lv[1].center())
                pdir = p1-p0
                norm = np.cross(pdir,np.array([0,0,1]))
                norm = norm/np.linalg.norm(norm)
                plt.annotate(str(k),xy=(xe,ye),xytext=(xe-norm[0]*eps,ye-norm[1]*eps),color='b')
        nx.draw_networkx_nodes(self,self.pos,node_color='b',node_size=50,alpha=0.5)
        nx.draw_networkx_edges(self,self.pos,width=3,edge_color='k')
        lpos = { k : (self.pos[k][0]+0.05,self.pos[k][1]+0.05) for k in self.pos}
        nx.draw_networkx_labels(self,lpos,font_size=18)

    def tile(self,iface=0,iedge=0,angle=np.pi):
        self.nnode = self.nnode + 1
        # create a new face from face with index iface
        new_face = self.lfaces[iface].copy()
        # get the active edge of iface
        # points : edge termination
        # vedge : edge vector (non normalized)
        # axed : mirror axis orthogonal to vedge
        ed = self.lfaces[iface].subshapes('Edge')[iedge]
        points = ed.poly()
        vedge = np.array(points[1]) - np.array(points[0])
        axed = np.cross(vedge,np.array([0,0,1]))
        # mirror new face w.r.t axed
        new_face = cm.mirrored(new_face,ed.center(),axed)
        # modify normal orientation
        new_face = cm.rotated(new_face,new_face.center(),(1,0,0),np.pi)


        # append new face in PlanarNet.lfaces
        # update underlying graph
        # node position at centroid of the face

        self.lfaces.append(new_face)
        self.add_node(self.nnode)
        self.pos[self.nnode] = new_face.center()[0:2]
        self.add_edge(iface,self.nnode,angle=angle,iedge=iedge)
        self.shell = cm.Shell(self.lfaces)

    def unfold(self):
        """ unfold edges of the PlanarNet

        TODO : mimic fold implementation

        Returns
        -------

        solid : A Solid

        """
        for edge in self.edges():
            if0  = edge[0]
            if1 = edge[1]
            ag = self.edge[if0][if1]['angle']
            iedge = self.edge[if0][if1]['iedge']
            ed = self.lfaces[if0].subshapes('Edge')[iedge]
            points = ed.poly()
            pdir = np.array(points[1]) - np.array(points[0])
            pabout = ed.center()
            self.lfaces[if1] = cm.rotated(self.lfaces[if1],pabout,pdir,-ag)

        # update faces centroid
        for iface in self.node:
            face = self.lfaces[iface]
            self.pos[iface] = face.center()[0:2]

        self.shell = cm.Shell(self.lfaces)
        self.folded = False

    def fold(self):
        """ fold edges of the PlanarNet

        Returns
        -------

        A solid or a coumpound of faces

        Notes
        -----

        This method fold the planar net w.r.t to the edge angles.
        It yields a shell member

        """
        for edge in self.edges():
            if0 = edge[0]
            if1 = edge[1]
            ag = self.edge[if0][if1]['angle']
            iedge = self.edge[if0][if1]['iedge']
            ed = self.lfaces[if0].subshapes('Edge')[iedge]
            points = ed.poly()
            pdir = np.array(points[1]) - np.array(points[0])
            pabout = ed.center()

            self.remove_edge(if0,if1)
            lgraphs = list(nx.connected_component_subgraphs(nx.Graph(self)))
            ln0 = lgraphs[0].node.keys()
            ln1 = lgraphs[1].node.keys()
            self.add_edge(if0,if1)
            if if1 in ln1:
                lfaces1 = ln1
            else:
                lfaces1 = ln0
            for f in lfaces1:
                self.lfaces[f] = cm.rotated(self.lfaces[f],pabout,pdir,ag)

        # update faces centroid in the Graph

        for iface in self.node:
            face = self.lfaces[iface]
            self.pos[iface] = face.center()[0:2]

        # creates the shell
        self.shell = cm.Shell(self.lfaces)

        self.folded = True

        asolid = cm.Solid([self.shell])

        return asolid


if __name__ == "__main__":
    p1 = PlanarNet()
    alpha = np.pi-np.arccos(1/3.)
    p1.tile(iedge=0, angle = alpha)
    p1.tile(iedge=1, angle = alpha)
    p1.tile(iedge=2, angle = alpha)
    tetra = p1.fold()
    tetra.to_html('tetraedre.html')
