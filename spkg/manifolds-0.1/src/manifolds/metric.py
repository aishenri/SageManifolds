r"""
Pseudo-Riemannian metrics

The class :class:`Metric` implements pseudo-Riemannian metrics on 
differentiable manifolds over `\RR`. 

Derived classes of :class:`Metric` are 

* :class:`RiemannMetric` for Riemannian metrics 
* :class:`LorentzMetric` for Lorentzian metrics 

AUTHORS:

- Eric Gourgoulhon, Michal Bejger (2013) : initial version


"""
#******************************************************************************
#       Copyright (C) 2013 Eric Gourgoulhon <eric.gourgoulhon@obspm.fr>
#       Copyright (C) 2013 Michal Bejger <bejger@camk.edu.pl>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#                  http://www.gnu.org/licenses/
#******************************************************************************

from manifold import Manifold
from tensorfield import TensorField
from rank2field import SymBilinFormField
from connection import LeviCivitaConnection
from diffform import DiffForm
from sage.rings.integer import Integer

class Metric(SymBilinFormField):
    r"""
    Base class for pseudo-Riemannian metrics on a differentiable manifold.

    INPUT:
    
    - ``manifold`` -- the manifold on which the metric is defined
    - ``name`` -- name given to the metric
    - ``signature`` -- (default: None) signature `S` of the metric as a single 
      integer: `S = n_+ - n_-`, where `n_+` (resp. `n_-`) is the number of 
      positive terms (resp. number of negative terms) in any diagonal writing 
      of the metric components; if ``signature`` is not provided, `S` is set to 
      the manifold's dimension (Riemannian signature)
    - ``latex_name`` -- (default: None) LaTeX symbol to denote the metric; if
      none, it is formed from ``name``      

    EXAMPLES:
    
    Metric on a 2-dimensional manifold::
    
        sage: m = Manifold(2, 'M', start_index=1)
        sage: c_xy = Chart(m, 'x y', 'xy')
        sage: g = Metric(m, 'g') ; g
        pseudo-Riemannian metric 'g' on the 2-dimensional manifold 'M'
        sage: latex(g)
        g
   
    A metric is a special kind of tensor field and therefore inheritates all the
    properties from class :class:`TensorField`::

        sage: isinstance(g, TensorField)
        True
        sage: g.tensor_type
        (0, 2)
        sage: g.symmetries()  # g is symmetric:
        symmetry: (0, 1);  no antisymmetry
        sage: isinstance(g, SymBilinFormField)  # a metric is actually a field of symmetric bilinear forms:
        True
       
    Setting the metric components in the manifold's default frame::
    
        sage: g[1,1], g[1,2], g[2,2] = 1+x, x*y, 1-x 
        sage: g[:]
        [ x + 1    x*y]
        [   x*y -x + 1]
        sage: g.show()
        g = (x + 1) dx*dx + x*y dx*dy + x*y dy*dx + (-x + 1) dy*dy

    Metric components in a frame different from the manifold's default one::
    
        sage: c_uv = Chart(m, 'u v', 'uv')  # new chart on M
        sage: xy_to_uv = CoordChange(c_xy, c_uv, x+y, x-y) ; xy_to_uv
        coordinate change from chart 'xy' (x, y) to chart 'uv' (u, v)
        sage: uv_to_xy = xy_to_uv.inverse() ; uv_to_xy
        coordinate change from chart 'uv' (u, v) to chart 'xy' (x, y)
        sage: m.get_atlas()
        {'xy': chart 'xy' (x, y), 'uv': chart 'uv' (u, v)}
        sage: m.frames
        {'xy_b': coordinate basis 'xy_b' (d/dx,d/dy), 'uv_b': coordinate basis 'uv_b' (d/du,d/dv)}
        sage: g.comp('uv_b')[:]  # metric components in frame 'uv_b' expressed in M's default chart (x,y)
        [ 1/2*x*y + 1/2          1/2*x]
        [         1/2*x -1/2*x*y + 1/2]
        sage: g.show('uv_b')
        g = (1/2*x*y + 1/2) du*du + 1/2*x du*dv + 1/2*x dv*du + (-1/2*x*y + 1/2) dv*dv
        sage: g.comp('uv_b')[:, 'uv']   # metric components in frame 'uv_b' expressed in chart (u,v)
        [ 1/8*u^2 - 1/8*v^2 + 1/2            1/4*u + 1/4*v]
        [           1/4*u + 1/4*v -1/8*u^2 + 1/8*v^2 + 1/2]
        sage: g.show('uv_b', 'uv')
        g = (1/8*u^2 - 1/8*v^2 + 1/2) du*du + (1/4*u + 1/4*v) du*dv + (1/4*u + 1/4*v) dv*du + (-1/8*u^2 + 1/8*v^2 + 1/2) dv*dv


    The inverse metric is obtained via :meth:`inverse`::
    
        sage: ig = g.inverse() ; ig
        tensor field 'inv_g' of type (2,0) on the 2-dimensional manifold 'M'
        sage: ig[:]
        [ (x - 1)/(x^2*y^2 + x^2 - 1)      x*y/(x^2*y^2 + x^2 - 1)]
        [     x*y/(x^2*y^2 + x^2 - 1) -(x + 1)/(x^2*y^2 + x^2 - 1)]
        sage: ig.show()
        inv_g = (x - 1)/(x^2*y^2 + x^2 - 1) d/dx*d/dx + x*y/(x^2*y^2 + x^2 - 1) d/dx*d/dy + x*y/(x^2*y^2 + x^2 - 1) d/dy*d/dx - (x + 1)/(x^2*y^2 + x^2 - 1) d/dy*d/dy

    """
    def __init__(self, manifold, name, signature=None, latex_name=None):
        SymBilinFormField.__init__(self, manifold, name, latex_name)
        # signature:
        ndim = self.manifold.dim
        if signature is None:
            signature = ndim
        else:
            if not isinstance(signature, (int, Integer)):
                raise TypeError("The metric signature must be an integer.")
            if (signature < - ndim) or (signature > ndim):
                raise ValueError("Metric signature out of range.")
            if (signature+ndim)%2 == 1:
                if ndim%2 == 0:
                    raise ValueError("The metric signature must be even.")
                else:
                    raise ValueError("The metric signature must be odd.")
        self._signature = signature
        # the pair (n_+, n_-):
        self._signature_pm = ((ndim+signature)/2, (ndim-signature)/2)
        self._indic_signat = 1 - 2*(self._signature_pm[1]%2)  # (-1)^n_-
        # inverse metric:
        inv_name = 'inv_' + self.name
        inv_latex_name = self.latex_name + r'^{-1}'
        self._inverse = TensorField(self.manifold, 2, 0, inv_name, 
                                    inv_latex_name, sym=(0,1))   
        self._connection = None  # Levi-Civita connection (not set yet)
        self._weyl = None # Weyl tensor (not set yet)
        self._determinants = {} # determinants in various frames
        self._sqrt_abs_dets = {} # sqrt(abs(det g)) in various frames
        self._vol_forms = [] # volume form and associated tensors
        
    def _repr_(self):
        r"""
        Special Sage function for the string representation of the object.
        """
        description = "pseudo-Riemannian metric '%s'" % self.name
        description += " on the " + str(self.manifold)
        return description

    def _new_instance(self):
        r"""
        Create a :class:`Metric` instance with the same signature.
        
        """
        return Metric(self.manifold, 'unnamed', signature=self._signature)


    def _del_derived(self):
        r"""
        Delete the derived quantities
        """
        # First the derived quantities from the mother class are deleted:
        SymBilinFormField._del_derived(self)
        # The inverse metric is cleared: 
        self._inverse.components.clear()
        self._inverse._del_derived()
        # The connection and Weyl tensor are reset to None:
        self._connection = None
        self._weyl = None
        # The dictionary of determinants over the various frames is cleared:
        self._determinants.clear()
        self._sqrt_abs_dets.clear()
        # The volume form and the associated tensors is deleted:
        del self._vol_forms[:]

    def signature(self):
        r"""
        Signature of the metric. 
        
        OUTPUT:

        - signature `S` of the metric, defined as the integer 
          `S = n_+ - n_-`, where `n_+` (resp. `n_-`) is the number of 
          positive terms (resp. number of negative terms) in any diagonal 
          writing of the metric components
        
        EXAMPLES:
        
        Signatures on a 2-dimensional manifold::
        
            sage: M = Manifold(2, 'M')
            sage: g = Metric(M, 'g') # if not specified, the signature is Riemannian
            sage: g.signature() 
            2
            sage: h = Metric(M, 'h', signature=0)
            sage: h.signature()
            0

        """
        return self._signature
        
    def inverse(self):
        r"""
        Return the inverse metric.
        
        EXAMPLES:
        
        Inverse metric on a 2-dimensional manifold::
    
            sage: m = Manifold(2, 'M', start_index=1)
            sage: c_xy = Chart(m, 'x y', 'xy')
            sage: g = Metric(m, 'g') 
            sage: g[1,1], g[1,2], g[2,2] = 1+x, x*y, 1-x 
            sage: g[:]  # components in the manifold's default frame
            [ x + 1    x*y]
            [   x*y -x + 1]
            sage: ig = g.inverse() ; ig
            tensor field 'inv_g' of type (2,0) on the 2-dimensional manifold 'M'
            sage: ig[:]
            [ (x - 1)/(x^2*y^2 + x^2 - 1)      x*y/(x^2*y^2 + x^2 - 1)]
            [     x*y/(x^2*y^2 + x^2 - 1) -(x + 1)/(x^2*y^2 + x^2 - 1)]

        If the metric is modified, the inverse metric is automatically updated::
        
            sage: g[1,2] = 0 ; g[:]
            [ x + 1      0]
            [     0 -x + 1]
            sage: g.inverse()[:]
            [ 1/(x + 1)          0]
            [         0 -1/(x - 1)]

        """
        from sage.matrix.constructor import matrix
        from component import CompFullySym
        from utilities import simplify_chain
        # Is the inverse metric up to date ?
        for frame_name in self.components:
            if frame_name not in self._inverse.components:
                # the computation is necessary
                manif = self.manifold
                if frame_name[-2:] == '_b':
                    # coordinate basis
                    chart_name = frame_name[:-2]
                else:
                    chart_name = manif.def_chart.name
                si = manif.sindex
                nsi = manif.dim + si
                try:    
                    gmat = matrix(
                              [[self.comp(frame_name)[i, j, chart_name].express 
                              for j in range(si, nsi)] for i in range(si, nsi)])
                except KeyError:
                    continue
                gmat_inv = gmat.inverse()
                cinv = CompFullySym(manif, 2, frame_name)
                for i in range(si, nsi):
                    for j in range(i, nsi):   # symmetry taken into account
                        cinv[i, j, chart_name] = simplify_chain(
                                                        gmat_inv[i-si,j-si])
                self._inverse.components[frame_name] = cinv
        return self._inverse
        
    def connection(self, name=None, latex_name=None):
        r"""
        Return the unique torsion-free affine connection compatible with 
        ``self``.
        
        This is the so-called Levi-Civita connection.
        
        INPUT:
        
        - ``name`` -- (default: None) name given to the Levi-Civita connection; 
          if none, it is formed from the metric name
        - ``latex_name`` -- (default: None) LaTeX symbol to denote the 
          Levi-Civita connection; if none, it is formed from the symbol 
          `\nabla` and the metric symbol
          
        OUTPUT:
        
        - the Levi-Civita connection, as an instance of 
          :class:`LeviCivitaConnection`. 
          
        EXAMPLES:
        
        Levi-Civitation connection associated with the Euclidean metric on 
        `\RR^3`::
        
            sage: m = Manifold(3, 'R^3', start_index=1)
            sage: # Let us use spherical coordinates on R^3:
            sage: c_spher = Chart(m, r'r:positive, th:positive:\theta, ph:\phi', 'spher')
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2], g[3,3] = 1, r^2 , (r*sin(th))^2  # the Euclidean metric
            sage: g.connection()
            Levi-Civita connection 'nabla_g' associated with the pseudo-Riemannian metric 'g' on the 3-dimensional manifold 'R^3'
            sage: g.connection()[:]  # Christoffel symbols in spherical coordinates
            [[[0, 0, 0], [0, -r, 0], [0, 0, -r*sin(th)^2]],
            [[0, 1/r, 0], [1/r, 0, 0], [0, 0, -sin(th)*cos(th)]],
            [[0, 0, 1/r], [0, 0, cos(th)/sin(th)], [1/r, cos(th)/sin(th), 0]]]

        Test of compatibility with the metric::
        
            sage: Dg = g.connection()(g) ; Dg
            tensor field 'nabla_g g' of type (0,3) on the 3-dimensional manifold 'R^3'
            sage: Dg == 0
            True
            sage: Dig = g.connection()(g.inverse()) ; Dig
            tensor field 'nabla_g inv_g' of type (2,1) on the 3-dimensional manifold 'R^3'
            sage: Dig == 0
            True
        
        """
        if self._connection is None:
            if name is None:
                name = 'nabla_' + self.name
            if latex_name is None:
                latex_name = r'\nabla_{' + self.latex_name + '}'
            self._connection = LeviCivitaConnection(self, name, latex_name)
        return self._connection

        
    def christoffel(self, chart_name=None):
        r"""
        Christoffel symbols of ``self`` with respect to a chart.
        
        INPUT:
        
        - ``chart_name`` -- (default: None) name of the chart; if none is 
          provided, the manifold's default chart is assumed.
          
        OUTPUT:
        
        - the set of Christoffel symbols in the given chart, as an instance of
          :class:`CompWithSym`
          
        EXAMPLES:
        
        Christoffel symbols of the flat metric on `\RR^3` with respect to 
        spherical coordinates::
        
            sage: m = Manifold(3, 'R3', r'\RR^3', start_index=1)
            sage: X = Chart(m, r'r:positive th:\theta  ph:\phi','spher')
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2], g[3,3] = 1, r^2, r^2*sin(th)^2
            sage: g.show()  # the standard flat metric expressed in spherical coordinates
            g = dr*dr + r^2 dth*dth + r^2*sin(th)^2 dph*dph
            sage: Gam = g.christoffel() ; Gam
            3-indices components w.r.t. the coordinate basis 'spher_b' (d/dr,d/dth,d/dph), with symmetry on the index positions (1, 2)
            sage: print type(Gam)
            <class 'sage.geometry.manifolds.component.CompWithSym'>
            sage: Gam[:]
            [[[0, 0, 0], [0, -r, 0], [0, 0, -r*sin(th)^2]],
             [[0, 1/r, 0], [1/r, 0, 0], [0, 0, -sin(th)*cos(th)]],
             [[0, 0, 1/r], [0, 0, cos(th)/sin(th)], [1/r, cos(th)/sin(th), 0]]]
            sage: Gam[1,2,2]
            -r
            sage: Gam[2,1,2]
            1/r
            sage: Gam[3,1,3]
            1/r
            sage: Gam[3,2,3]
            cos(th)/sin(th)
            sage: Gam[2,3,3]
            -sin(th)*cos(th)

        
        """
        if chart_name is None:
            frame_name = self.manifold.def_chart.frame.name
        else:
            frame_name = self.manifold.atlas[chart_name].frame.name
        return self.connection().coef(frame_name)
          
    def riemann(self, frame_name=None, name=None, latex_name=None):
        r""" 
        Return the Riemann curvature tensor associated with the metric.

        This method is actually a shortcut for ``self.connection().riemann()``
        
        The Riemann curvature tensor is the tensor field `R` of type (1,3) 
        defined by

        .. MATH::
            
            R(\omega, u, v, w) = \left\langle \omega, \nabla_u \nabla_v w
                - \nabla_v \nabla_u w - \nabla_{[u, v]} w \right\rangle
        
        for any 1-form  `\omega`  and any vector fields `u`, `v` and `w`. 

        INPUT:
        
        - ``frame_name`` -- (default: None) string containing the name of the 
          vector frame in which the computation must be performed; if none is 
          provided, the computation is performed in a frame for which the 
          metric components are known, privileging the manifold's default 
          frame.
        - ``name`` -- (default: None) name given to the Riemann tensor; 
          if none, it is set to "Riem(g)", where "g" is the metric's name
        - ``latex_name`` -- (default: None) LaTeX symbol to denote the 
          Riemann tensor; if none, it is set to "\\mathrm{Riem}(g)", where "g" 
          is the metric's name

        OUTPUT:
        
        - the Riemann curvature tensor `R`, as an instance of 
          :class:`TensorField`
        
        EXAMPLES:

        Riemann tensor of the standard metric on the 2-sphere::
        
            sage: m = Manifold(2, 'S^2', start_index=1)
            sage: c_spher = Chart(m, r'th:\theta, ph:\phi', 'spher')
            sage: a = var('a') # the sphere radius 
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2] = a^2, a^2*sin(th)^2
            sage: g.show() # standard metric on the 2-sphere of radius a:
            g = a^2 dth*dth + a^2*sin(th)^2 dph*dph
            sage: g.riemann()
            tensor field 'Riem(g)' of type (1,3) on the 2-dimensional manifold 'S^2'
            sage: g.riemann()[:]
            [[[[0, 0], [0, 0]], [[0, sin(th)^2], [-sin(th)^2, 0]]],
             [[[0, (cos(th)^2 - 1)/sin(th)^2], [1, 0]], [[0, 0], [0, 0]]]]
             
        In dimension 2, the Riemann tensor can be expressed entirely in terms of
        the Ricci scalar `r`:

        .. MATH::
            
            R^i_{\ \, jlk} = \frac{r}{2} \left( \delta^i_{\ \, k} g_{jl}
                - \delta^i_{\ \, l} g_{jk} \right)
        
        This formula can be checked here, with the r.h.s. rewritten as 
        `-r g_{j[k} \delta^i_{\ \, l]}`::
        
            sage: g.riemann() == -g.ricci_scalar()*(g*IdentityMap(m)).antisymmetrize([2,3])
            True
        
        """
        return self.connection().riemann(frame_name, name, latex_name)

        
    def ricci(self, frame_name=None, name=None, latex_name=None):
        r""" 
        Return the Ricci tensor associated with the metric.
        
        This method is actually a shortcut for ``self.connection().ricci()``
                
        The Ricci tensor is the tensor field `Ric` of type (0,2) 
        defined from the Riemann curvature tensor `R` by 

        .. MATH::
            
            Ric(u, v) = R(e^i, u, e_i, v)
        
        for any vector fields `u` and `v`, `(e_i)` being any vector frame and
        `(e^i)` the dual coframe. 

        INPUT:
        
        - ``frame_name`` -- (default: None) string containing the name of the 
          vector frame in which the computation must be performed; if none is 
          provided, the computation is performed in a frame for which the 
          metric components are known, privileging the manifold's default 
          frame.
        - ``name`` -- (default: None) name given to the Ricci tensor; 
          if none, it is set to "Ric(g)", where "g" is the metric's name
        - ``latex_name`` -- (default: None) LaTeX symbol to denote the 
          Ricci tensor; if none, it is set to "\\mathrm{Ric}(g)", where "g" 
          is the metric's name
          
        OUTPUT:
        
        - the Ricci tensor `Ric`, as an instance of :class:`SymBilinFormField`
        
        EXAMPLES:
        
        Ricci tensor of the standard metric on the 2-sphere::
        
            sage: m = Manifold(2, 'S^2', start_index=1)
            sage: c_spher = Chart(m, r'th:\theta, ph:\phi', 'spher')
            sage: a = var('a') # the sphere radius 
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2] = a^2, a^2*sin(th)^2
            sage: g.show() # standard metric on the 2-sphere of radius a:
            g = a^2 dth*dth + a^2*sin(th)^2 dph*dph
            sage: g.ricci()
            field of symmetric bilinear forms 'Ric(g)' on the 2-dimensional manifold 'S^2'
            sage: g.ricci()[:]
            [        1         0]
            [        0 sin(th)^2]
            sage: g.ricci() == a^(-2) * g
            True

        """
        return self.connection().ricci(frame_name, name, latex_name)
    
        
    def ricci_scalar(self, frame_name=None, name=None, latex_name=None):
        r""" 
        Return the Ricci scalar associated with the metric.
        
        The Ricci scalar is the scalar field `r` defined from the Ricci tensor 
        `Ric` and the metric tensor `g` by 

        .. MATH::
            
            r = g^{ij} Ric_{ij}
        

        INPUT:
        
        - ``frame_name`` -- (default: None) string containing the name of the 
          vector frame in which the computation must be performed; if none is 
          provided, the computation is performed in a frame for which the 
          metric components are known, privileging the manifold's default 
          frame.
        - ``name`` -- (default: None) name given to the Ricci scalar; 
          if none, it is set to "r(g)", where "g" is the metric's name
        - ``latex_name`` -- (default: None) LaTeX symbol to denote the 
          Ricci scalar; if none, it is set to "\\mathrm{r}(g)", where "g" 
          is the metric's name

        OUTPUT:
        
        - the Ricci scalar `r`, as an instance of :class:`ScalarField`

        EXAMPLES:
        
        Ricci scalar of the standard metric on the 2-sphere::
        
            sage: m = Manifold(2, 'S^2', start_index=1)
            sage: c_spher = Chart(m, r'th:\theta, ph:\phi', 'spher')
            sage: a = var('a') # the sphere radius 
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2] = a^2, a^2*sin(th)^2
            sage: g.show() # standard metric on the 2-sphere of radius a:
            g = a^2 dth*dth + a^2*sin(th)^2 dph*dph
            sage: g.ricci_scalar()
            scalar field 'r(g)' on the 2-dimensional manifold 'S^2'
            sage: g.ricci_scalar().expr()
            2/a^2

        """
        return self.connection().ricci_scalar(frame_name, name, latex_name)


    def weyl(self, name=None, latex_name=None):
        r""" 
        Return the Weyl conformal tensor associated with the metric.
                        
        The Weyl conformal tensor is the tensor field `C` of type (1,3) 
        defined as the trace-free part of the Riemann curvature tensor `R`

        INPUT:
        
        - ``name`` -- (default: None) name given to the Weyl conformal tensor; 
          if none, it is set to "C(g)", where "g" is the metric's name
        - ``latex_name`` -- (default: None) LaTeX symbol to denote the 
          Weyl conformal tensor; if none, it is set to "\\mathrm{C}(g)", where 
          "g" is the metric's name

        OUTPUT:
        
        - the Weyl conformal tensor `C`, as an instance of :class:`TensorField`
        
        EXAMPLES:
        
        Checking that the Weyl tensor identically vanishes on a 3-dimensional 
        manifold, for instance the hyperbolic space `H^3`::
        
            sage: m = Manifold(3, 'H^3', start_index=1)
            sage: X = Chart(m, r'rh:positive:\rho th:\theta  ph:\phi', 'rtp-coord')
            sage: g = Metric(m, 'g')
            sage: b = var('b')                                                        
            sage: g[1,1], g[2,2], g[3,3] = b^2, (b*sinh(rh))^2, (b*sinh(rh)*sin(th))^2
            sage: g.show()  # standard metric on H^3:
            g = b^2 drh*drh + b^2*sinh(rh)^2 dth*dth + b^2*sin(th)^2*sinh(rh)^2 dph*dph
            sage: C = g.weyl() ; C
            tensor field 'C(g)' of type (1,3) on the 3-dimensional manifold 'H^3'
            sage: C == 0 
            True

        """
        from rank2field import IdentityMap
        if self._weyl is None:
            n = self.manifold.dim
            if n < 3:
                raise ValueError("The Weyl tensor is not defined for a " + 
                                 "manifold of dimension n <= 2.")
            delta = IdentityMap(self.manifold)
            riem = self.riemann()
            ric = self.ricci()
            rscal = self.ricci_scalar()
            # First index of the Ricci tensor raised with the metric
            ricup = ric.up(self, 0) 
            # The identity map is expressed in a frame in which the Riemann 
            # tensor is known
            delta.comp(riem.pick_a_frame())
            aux = self*ricup + ric*delta - rscal/(n-1)* self*delta
            self._weyl = riem + 2/(n-2)* aux.antisymmetrize([2,3]) 
            if name is None:
                self._weyl.name = "C(" + self.name + ")"
            else:
                self._weyl.name = name
            if latex_name is None:
                self._weyl.latex_name = r"\mathrm{C}\left(" + self.latex_name + r"\right)"
            else:
                self._weyl.latex_name = latex_name
        return self._weyl
            
    def determinant(self, frame_name=None):
        r"""
        Determinant of the metric components in the specified frame.
        
        INPUT:
        
        - ``frame_name`` -- (default: None) name of the vector frame with 
          respect to which the components `g_{ij}` of ``self`` are defined; 
          if None, the manifold's default frame is used. If a chart name is 
          provided, the associated coordinate basis is used
          
        OUTPUT:
        
        - the determinant `\det (g_{ij})`, as an instance of :class:`ScalarField`
        
        EXAMPLES:
        
        Metric determinant on a 2-dimensional manifold::
        
            sage: M = Manifold(2, 'M', start_index=1)
            sage: X = Chart(M, 'x y', 'xy')
            sage: g = Metric(M, 'g')
            sage: g[1,1], g[1, 2], g[2, 2] = 1+x, x*y , 1-y
            sage: g[:]
            [ x + 1    x*y]
            [   x*y -y + 1]
            sage: s = g.determinant()  # determinant in M's default frame
            sage: s.expr()
            -x^2*y^2 - (x + 1)*y + x + 1

        Determinant in a frame different from the default's one::
            
            sage: Y = Chart(M, 'u v', 'uv')
            sage: ch_X_Y = CoordChange(X, Y, x+y, x-y)   
            sage: ch_X_Y.inverse()                    
            coordinate change from chart 'uv' (u, v) to chart 'xy' (x, y)
            sage: g.comp('uv_b')[:, 'uv']
            [ 1/8*u^2 - 1/8*v^2 + 1/4*v + 1/2                            1/4*u]
            [                           1/4*u -1/8*u^2 + 1/8*v^2 + 1/4*v + 1/2]
            sage: g.determinant('uv_b').expr()
            -1/4*x^2*y^2 - 1/4*(x + 1)*y + 1/4*x + 1/4
            sage: g.determinant('uv_b').expr('uv')
            -1/64*u^4 - 1/16*u^2 - 1/64*v^4 + 1/32*(u^2 + 2)*v^2 + 1/4*v + 1/4

        The name of a chart can be passed instead of the name of a frame::
        
            sage: g.determinant('xy') is g.determinant('xy_b')
            True
            sage: g.determinant('uv') is g.determinant('uv_b')
            True

        The metric determinant depends on the frame::
        
            sage: g.determinant('xy_b') == g.determinant('uv_b')
            False
        
        """
        from sage.matrix.constructor import matrix
        from scalarfield import ScalarField
        from utilities import simple_determinant, simplify_chain
        manif = self.manifold
        if frame_name is None:
            frame_name = manif.def_frame.name
        if frame_name in manif.atlas:   
            # frame_name is actually the name of a chart and is changed to the
            # name of the associated coordinate basis:
            frame_name = manif.atlas[frame_name].frame.name
        if frame_name not in self._determinants:
            # a new computation is necessary
            resu = ScalarField(manif)
            gg = self.comp(frame_name)
            i1 = manif.sindex
            for chart_name in gg[[i1, i1]].express:
                gm = matrix( [[ gg[i, j, chart_name].express 
                            for j in manif.irange()] for i in manif.irange()] )
                detgm = simplify_chain(simple_determinant(gm))
                resu.set_expr(detgm, chart_name=chart_name, 
                              delete_others=False)
            self._determinants[frame_name] = resu
        return self._determinants[frame_name]

    def sqrt_abs_det(self, frame_name=None):
        r"""
        Square root of the absolute value of the determinant of the metric 
        components in the specified frame.
        
        INPUT:
        
        - ``frame_name`` -- (default: None) name of the vector frame with 
          respect to which the components `g_{ij}` of ``self`` are defined; 
          if None, the manifold's default frame is used. If a chart name is 
          provided, the associated coordinate basis is used
          
        OUTPUT:
        
        -  `\sqrt{|\det (g_{ij})|}`, as an instance of :class:`ScalarField`
        
        EXAMPLES:
        
        Standard metric in the Euclidean space `\RR^3` with spherical 
        coordinates::
        
            sage: m = Manifold(3, 'M', start_index=1)
            sage: c_spher = Chart(m, r'r:positive th:positive:\theta ph:\phi', 'spher')
            sage: assume(th>=0); assume(th<=pi)
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2], g[3,3] = 1, r^2, (r*sin(th))^2
            sage: g.show()
            g = dr*dr + r^2 dth*dth + r^2*sin(th)^2 dph*dph
            sage: g.sqrt_abs_det().expr()
            r^2*sin(th)
            
        Metric determinant on a 2-dimensional manifold::
        
            sage: M = Manifold(2, 'M', start_index=1)
            sage: X = Chart(M, 'x y', 'xy')
            sage: g = Metric(M, 'g')
            sage: g[1,1], g[1, 2], g[2, 2] = 1+x, x*y , 1-y
            sage: g[:]
            [ x + 1    x*y]
            [   x*y -y + 1]
            sage: s = g.sqrt_abs_det() ; s
            scalar field on the 2-dimensional manifold 'M'
            sage: s.expr()
            sqrt(-x^2*y^2 - (x + 1)*y + x + 1)

        Determinant in a frame different from the default's one::
            
            sage: Y = Chart(M, 'u v', 'uv')
            sage: ch_X_Y = CoordChange(X, Y, x+y, x-y)   
            sage: ch_X_Y.inverse()                    
            coordinate change from chart 'uv' (u, v) to chart 'xy' (x, y)
            sage: g.comp('uv_b')[:, 'uv']
            [ 1/8*u^2 - 1/8*v^2 + 1/4*v + 1/2                            1/4*u]
            [                           1/4*u -1/8*u^2 + 1/8*v^2 + 1/4*v + 1/2]
            sage: g.sqrt_abs_det('uv_b').expr()
            1/2*sqrt(-x^2*y^2 - (x + 1)*y + x + 1)
            sage: g.sqrt_abs_det('uv_b').expr('uv')
            1/8*sqrt(-u^4 - 4*u^2 - v^4 + 2*(u^2 + 2)*v^2 + 16*v + 16)

        The name of a chart can be passed instead of the name of a frame::
        
            sage: g.sqrt_abs_det('uv') is g.sqrt_abs_det('uv_b')
            True

        The metric determinant depends on the frame::
        
            sage: g.sqrt_abs_det('xy_b') == g.sqrt_abs_det('uv_b') 
            False

        """
        from sage.functions.other import sqrt
        from scalarfield import ScalarField
        from utilities import simplify_chain
        manif = self.manifold
        if frame_name is None:
            frame_name = manif.def_frame.name
        if frame_name in manif.atlas:   
            # frame_name is actually the name of a chart and is changed to the
            # name of the associated coordinate basis:
            frame_name = manif.atlas[frame_name].frame.name
        if frame_name not in self._sqrt_abs_dets:
            # a new computation is necessary
            detg = self.determinant(frame_name)
            resu = ScalarField(manif)
            for chart_name in detg.express:
                x = self._indic_signat * detg.express[chart_name].express # |g|
                x = simplify_chain(sqrt(x))
                resu.set_expr(x, chart_name=chart_name, delete_others=False)
            self._sqrt_abs_dets[frame_name] = resu
        return self._sqrt_abs_dets[frame_name]


    def volume_form(self, contra=0):
        r"""
        Volume form (Levi-Civita tensor) `\epsilon` associated with the metric.
        
        This assumes that the manifold is orientable. 
        
        The volume form `\epsilon` is a `n`-form (`n` being the manifold's 
        dimension) such that for any vector basis `(e_i)` that is orthonormal
        with respect to the metric, 
        
        .. MATH::
            
            \epsilon(e_1,\ldots,e_n) = \pm 1 

        There are only two such `n`-forms, which are opposite of each other. 
        The volume form `\epsilon` is selected such that the manifold's default 
        frame is right-handed with respect to it. 
        
        INPUT:
        
        - ``contra`` -- (default: 0) number of contravariant indices of the
          returned tensor
        
        OUTPUT:
        
        - if ``contra = 0`` (default value): the volume `n`-form `\epsilon`, as 
          an instance of :class:`DiffForm`
        - if ``contra = k``, with `1\leq k \leq n`, the tensor field of type 
          (k,n-k) formed from `\epsilon` by raising the first k indices with the 
          metric (see method :meth:`TensorField.up`); the output is then an
          instance of :class:`TensorField`, with the appropriate antisymmetries
       
        EXAMPLES:
        
        Volume form on `\RR^3` with spherical coordinates::
        
            sage: m = Manifold(3, 'M', start_index=1)
            sage: c_spher = Chart(m, r'r:positive th:positive:\theta ph:\phi', 'spher')
            sage: assume(th>=0); assume(th<=pi)
            sage: g = Metric(m, 'g')
            sage: g[1,1], g[2,2], g[3,3] = 1, r^2, (r*sin(th))^2
            sage: g.show()
            g = dr*dr + r^2 dth*dth + r^2*sin(th)^2 dph*dph
            sage: eps = g.volume_form() ; eps
            3-form 'eps_g' on the 3-dimensional manifold 'M'
            sage: eps.show()
            eps_g = r^2*sin(th) dr/\dth/\dph
            sage: eps[[1,2,3]] == g.sqrt_abs_det()
            True
            sage: latex(eps)
            \epsilon_{g}
            
            
        The tensor field of components `\epsilon^i_{\ \, jk}` (``contra=1``)::
        
            sage: eps1 = g.volume_form(1) ; eps1
            tensor field of type (1,2) on the 3-dimensional manifold 'M'
            sage: eps1.symmetries()
            no symmetry;  antisymmetry: (1, 2)
            sage: eps1[:]
            [[[0, 0, 0], [0, 0, r^2*sin(th)], [0, -r^2*sin(th), 0]],
             [[0, 0, -sin(th)], [0, 0, 0], [sin(th), 0, 0]],
             [[0, 1/sin(th), 0], [-1/sin(th), 0, 0], [0, 0, 0]]]
            
        The tensor field of components `\epsilon^{ij}_{\ \ k}` (``contra=2``)::
        
            sage: eps2 = g.volume_form(2) ; eps2
            tensor field of type (2,1) on the 3-dimensional manifold 'M'
            sage: eps2.symmetries()
            no symmetry;  antisymmetry: (0, 1)
            sage: eps2[:]
            [[[0, 0, 0], [0, 0, sin(th)], [0, -1/sin(th), 0]],
             [[0, 0, -sin(th)], [0, 0, 0], [1/(r^2*sin(th)), 0, 0]],
             [[0, 1/sin(th), 0], [-1/(r^2*sin(th)), 0, 0], [0, 0, 0]]]
            
        The tensor field of components `\epsilon^{ijk}` (``contra=3``)::
        
            sage: eps3 = g.volume_form(3) ; eps3
            tensor field of type (3,0) on the 3-dimensional manifold 'M'
            sage: eps3.symmetries()
            no symmetry;  antisymmetry: (0, 1, 2)
            sage: eps3[:]
            [[[0, 0, 0], [0, 0, 1/(r^2*sin(th))], [0, -1/(r^2*sin(th)), 0]],
             [[0, 0, -1/(r^2*sin(th))], [0, 0, 0], [1/(r^2*sin(th)), 0, 0]],
             [[0, 1/(r^2*sin(th)), 0], [-1/(r^2*sin(th)), 0, 0], [0, 0, 0]]]
            sage: eps3[1,2,3]
            1/(r^2*sin(th))
            sage: eps3[[1,2,3]] * g.sqrt_abs_det() == 1
            True
        
        """
        if self._vol_forms == []:
            # a new computation is necessary
            manif = self.manifold
            ndim = manif.dim
            eps = DiffForm(manif, ndim, name='eps_'+self.name, 
                           latex_name=r'\epsilon_{'+self.latex_name+r'}')
            ind = tuple(range(manif.sindex, manif.sindex+ndim))
            eps[[ind]] = self.sqrt_abs_det(manif.def_frame.name)
            self._vol_forms.append(eps)  # Levi-Civita tensor constructed
            # Tensors related to the Levi-Civita one by index rising:
            for k in range(1, ndim+1):
                epskm1 = self._vol_forms[k-1]
                epsk = epskm1.up(self, k-1)
                if k > 1:
                    # restoring the antisymmetry after the up operation: 
                    epsk = epsk.antisymmetrize(range(k)) 
                self._vol_forms.append(epsk)
        return self._vol_forms[contra]


#*****************************************************************************

class RiemannMetric(Metric):
    r"""
    Riemannian metric on a differentiable manifold.
    
    A Riemannian metric is a field of positive-definite symmetric bilinear 
    forms on the manifold. 

    See :class:`Metric` for a complete documentation. 
    
    INPUT:
    
    - ``manifold`` -- the manifold on which the metric is defined
    - ``name`` -- name given to the metric
    - ``latex_name`` -- (default: None) LaTeX symbol to denote the metric; if
      none, it is formed from ``name``      

    EXAMPLE:
    
    Standard metric on the 2-sphere `S^2`::
    
        sage: m = Manifold(2, 'S^2', start_index=1)
        sage: c_spher = Chart(m, r'th:\theta, ph:\phi', 'spher')
        sage: g = RiemannMetric(m, 'g') ; g
        Riemannian metric 'g' on the 2-dimensional manifold 'S^2'
        sage: g[1,1], g[2,2] = 1, sin(th)^2
        sage: g.show()
        g = dth*dth + sin(th)^2 dph*dph
        sage: g.signature() 
        2

    """
    def __init__(self, manifold, name, latex_name=None):
        Metric.__init__(self, manifold, name, signature=manifold.dim, 
                        latex_name=latex_name)
    
    def _repr_(self):
        r"""
        Special Sage function for the string representation of the object.
        """
        description = "Riemannian metric '%s'" % self.name
        description += " on the " + str(self.manifold)
        return description

    def _new_instance(self):
        r"""
        Create a :class:`RiemannMetric` instance on the same manifold.
        
        """
        return RiemannMetric(self.manifold, 'unnamed')


#*****************************************************************************

class LorentzMetric(Metric):
    r"""
    Lorentzian metric on a differentiable manifold.
    
    A Lorentzian metric is a field of symmetric bilinear 
    forms with signature `(-,+,\cdots,+)` or `(+,-,\cdots,-)`. 

    See :class:`Metric` for a complete documentation. 
    
    INPUT:
    
    - ``manifold`` -- the manifold on which the metric is defined
    - ``name`` -- name given to the metric
    - ``signature`` -- (default: 'positive') sign of the metric signature: 
        * if set to 'positive', the signature is n-2, where n is the manifold's
          dimension, i.e. `(-,+,\cdots,+)`
        * if set to 'negative', the signature is -n+2, i.e. `(+,-,\cdots,-)`
    - ``latex_name`` -- (default: None) LaTeX symbol to denote the metric; if
      none, it is formed from ``name``      

    EXAMPLE:
    
    Metric in Minkowski spacetime::
    
        sage: m = Manifold(4, 'M')
        sage: c_cart = Chart(m, 't x y z', 'cart')
        sage: g = LorentzMetric(m, 'g') ; g
        Lorentzian metric 'g' on the 4-dimensional manifold 'M'
        sage: g[0,0], g[1,1], g[2,2], g[3,3] = -1, 1, 1, 1
        sage: g.show()
        g = -dt*dt + dx*dx + dy*dy + dz*dz
        sage: g.signature()
        2
        
    The negative signature convention can be chosen::
    
        sage: g = LorentzMetric(m, 'g', signature='negative') 
        sage: g.signature()
        -2

    """
    def __init__(self, manifold, name, signature='positive', latex_name=None):
        if signature=='positive':
            signat = manifold.dim - 2
        else:
            signat = 2 - manifold.dim
        Metric.__init__(self, manifold, name, signature=signat,
                        latex_name=latex_name)


    def _repr_(self):
        r"""
        Special Sage function for the string representation of the object.
        """
        description = "Lorentzian metric '%s'" % self.name
        description += " on the " + str(self.manifold)
        return description

    def _new_instance(self):
        r"""
        Create a :class:`LorentzMetric` instance on the same manifold.
        
        """
        if self._signature >= 0:
            signature_type = 'positive'
        else:
            signature_type = 'negative'            
        return LorentzMetric(self.manifold, 'unnamed', signature=signature_type)






