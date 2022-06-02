from t2data import *
from mulgrids import *

class t2dataSub(t2data):
    def write_history_blocks(self, outfile):
        if self.history_block:
            outfile.write('FOFT\n')
            for blk in self.history_block:
                if isinstance(blk, str): blkname = blk
                else: blkname = blk.name
                outfile.write(unfix_blockname(blkname) + '        -1\n') # modified by matsunaga 2021.2.23
            outfile.write('\n')

    def write_history_connections(self, outfile):
        if self.history_connection:
            outfile.write('COFT\n')
            for con in self.history_connection:
                if isinstance(con, tuple): cname = con
                else: cname = tuple([blk.name for blk in con.block])
                outfile.write(unfix_blockname(cname[0]) + unfix_blockname(cname[1]) + '             -1\n') # modified by matsunaga 2021.2.23
            outfile.write('\n')
    
    def write_generator(self, gen, outfile):
        from copy import copy
        genw = copy(gen.__dict__)
        genw['name']  = unfix_blockname(genw['name'])
        genw['block'] = unfix_blockname(genw['block'])
        if genw['ex'] == 0: genw['ex'] = None
        if genw['hg'] == 0: genw['hg'] = None
        if genw['fg'] == 0: genw['fg'] = None
        outfile.write_value_line(genw, 'generator')
        if gen.ltab and gen.type != 'DELV': ntimes = abs(gen.ltab)
        else: ntimes = 1
        if ntimes > 1:
            nlines = int(ceil(ntimes / 4.))
            for i in range(nlines):
                i1, i2 = i * 4, min((i + 1) * 4, ntimes)
                vals = list(gen.time[i1: i2])
                if len(vals) < 4: vals += [None] * (4 - len(vals))
                outfile.write_values(vals, 'generation_times')
            for i in range(nlines):
                i1, i2 = i * 4, min((i + 1) * 4, ntimes)
                vals = list(gen.rate[i1: i2])
                if len(vals) < 4: vals += [None] * (4 - len(vals))
                outfile.write_values(vals, 'generation_rates')
            if gen.enthalpy:
                for i in range(nlines):
                    i1, i2 = i * 4, min((i + 1) * 4, ntimes)
                    vals = list(gen.enthalpy[i1: i2])
                    if len(vals) < 4: vals += [None] * (4 - len(vals))
                    outfile.write_values(vals, 'generation_enthalpy')


class mulgridSubVoronoiAmesh(mulgrid):
    def triangulate_column(self, column_name, replace = True,
                           chars = ascii_lowercase, spaces = True):
        """Replaces specified column with triangulated columns based on a new
        node at its centre, and returns list of new columns created.
        """
        ## fit_surface()から呼び出される場合、charsがなぜかtrue
        chars = ascii_lowercase + ascii_uppercase
        ##
        colnodelist = []
        col = self.column[column_name]
        for i, node in enumerate(col.node):
            inext = col.index_plus(i, 1)
            colnodelist.append((i, inext, 'c'))
        colnames = self.subdivide_column(column_name, 0, colnodelist, chars, spaces)
        return colnames

    def decompose_column(self, column_name, chars = ascii_lowercase,
                         spaces = True):
        """Replaces specified column with triangular or quadrilateral columns
        covering the original one, and returns a list of the new
        columns.  There are special cases for columns with lower
        numbers of sides, and 'straight' nodes (i.e. nodes that are on
        a straight line between their adjacent nodes).  Returns a list
        of names of columns that decompose the original column.
        """
        col = self.column[column_name]
        nn = col.num_nodes
        if nn <= 4: return [column_name]
        elif nn <= 8:
            angles = col.interior_angles
            tol = 1.e-3
            straight = [i for i, angle in enumerate(angles) if angle > np.pi - tol]
            ns = len(straight)
            if (nn, ns) == (5, 1):
                return self.subdivide_column(column_name, straight[0],
                                             [(0, 1, 2), (0, 2, 3), (0, 3, 4)],
                                             chars, spaces)
            elif (nn, ns) == (6, 2):
                d = col.index_dist(straight[0], straight[1])
                if d == 2:
                    last2 = [col.index_minus(i, 2) for i in straight]
                    start = [s for s, l in zip(straight, last2) if l not in straight][0]
                    return self.subdivide_column(column_name, start,
                                                 [(0, 1, 2, 'c'), (2, 3, 'c'),
                                                  (3, 4, 'c'), (4, 5, 'c'),
                                                  (5, 0, 'c')], chars, spaces)
                elif d == 3:
                    return self.subdivide_column(column_name, straight[0],
                                                 [(0, 1, 2, 3), (3, 4, 5, 0)],
                                                 chars, spaces)
                else: return self.triangulate_column(column_name, chars, spaces)
            elif (nn, ns) == (7, 3):
                last2 = [col.index_minus(i, 2) for i in straight]
                start = [s for s, l in zip(straight, last2) if l not in straight][0]
                return self.subdivide_column(column_name, start,
                                             [(0, 1, 2), (2, 3, 4),
                                              (0, 2, 4), (4, 5, 6, 0)],
                                             chars, spaces)
            elif (nn, ns) == (8, 4):
                return self.subdivide_column(column_name, straight[0],
                                             [(1, 2, 'c', 0), (2, 3, 4, 'c'),
                                              (4, 5, 6, 'c'), (6, 7, 0, 'c')],
                                             chars, spaces)
            else: return self.triangulate_column(column_name, chars, spaces)
        else: return self.triangulate_column(column_name, chars, spaces)


    def fit_columns(self, data, alpha = 0.1, beta = 0.1, columns = [],
                    min_columns = [], grid_boundary = False,
                    silent = False, output_dict = False):
        """Fits scattered data to the column centres of the geometry, using
        least-squares bilinear finite element fitting with Sobolev
        smoothing.  The parameter data should be in the form of a
        3-column array with x,y,z data in each row.  The smoothing
        parameters alpha and beta control the first and second
        derivatives of the surface.  If the parameter columns is
        specified, data will only be fitted for the specified column
        names.  For columns with names in min_columns, column centre
        values will be calculated as the minimum of the fitted nodal
        values.  For all other columns, the average of the nodal
        values is used.  If grid_boundary is True, only data inside
        the bounding polygon of the grid are used- this can speed up
        the fitting if there are many data outside the grid, and the
        grid has a simply-shaped boundary.  The result is by default
        an array of fitted values corresponding to each of the
        columns. If output_dict is True, the result is a dictionary of
        fitted values indexed by column names.
        """

        if columns == []: columns = self.columnlist
        else: 
            if isinstance(columns[0], str):
                columns = [self.column[col] for col in columns]
        if min_columns != []:
            if not isinstance(min_columns[0], str):
                min_columns = [col.name for col in min_columns]

        # make copy of geometry and decompose into 3, 4 sided columns:
        geo = mulgridSubVoronoiAmesh(convention = self.convention)
        for n in self.nodelist: geo.add_node(node(n.name, n.pos))
        for col in self.columnlist:
            geo.add_column(column(col.name, [geo.node[n.name] for n in col.node]))
        colmap = geo.decompose_columns(columns, mapping = True,
                                       chars = ascii_lowercase + ascii_uppercase,
                                       spaces = True)
        geo_columns = []
        for col in columns: geo_columns += [geo.column[geocol] for
                                            geocol in colmap[col.name]]

        nodes = geo.nodes_in_columns(geo_columns)
        node_index = dict([(n.name, i) for i, n in enumerate(nodes)])
        num_nodes = len(nodes)
        # assemble least squares FEM fitting system:
        from scipy import sparse
        A = sparse.lil_matrix((num_nodes, num_nodes))
        b = np.zeros(num_nodes)
        guess = None
        if grid_boundary: bounds = geo.boundary_polygon
        else: bounds = None
        qtree = geo.column_quadtree(columns)
        nd = len(data)
        for idata, d in enumerate(data):
            col = geo.column_containing_point(d[0:2], geo_columns,
                                              guess, bounds, qtree)
            percent = 100. * idata / nd
            if not silent:
                ps = 'fit_columns %3.0f%% done'% percent
                sys.stdout.write('%s\r' % ps)
                sys.stdout.flush()
            if col:
                xi = col.local_pos(d[0:2])
                if xi is not None:
                    guess = col
                    psi = col.basis(xi)
                    for i, nodei in enumerate(col.node):
                        I = node_index[nodei.name]
                        for j, nodej in enumerate(col.node):
                            J = node_index[nodej.name]
                            A[I, J] += psi[i] * psi[j]
                        b[I] += psi[i] * d[2]

        # add smoothing:
        smooth = {3: 0.5 * alpha * np.array([[1., 0., -1.], 
                                             [0., 1., -1.],
                                             [-1., -1., 2.]]),
                  4: alpha / 6. * np.array([[4., -1., -2., -1.],
                                            [-1., 4., -1., -2.],
                                            [-2., -1., 4., -1.],
                                            [-1., -2., -1., 4.]]) + \
                      beta * np.array([[1., -1., 1., -1.],
                                       [-1., 1., -1., 1.],
                                       [1., -1., 1., -1.],
                                       [-1., 1., -1., 1.]])}
        for col in geo_columns:
            for i, nodei in enumerate(col.node):
                I = node_index[nodei.name]
                for j, nodej in enumerate(col.node):
                    J = node_index[nodej.name]
                    A[I, J] += smooth[col.num_nodes][i, j]

        A = A.tocsr()
        from scipy.sparse.linalg import spsolve, use_solver
        use_solver(useUmfpack = False)
        z = spsolve(A, b)

        column_values = []
        def colnodez(col): return [z[node_index[node.name]] for node in col.node]
        for col in columns:
            if col.name in min_columns:
                geocol_min = None
                for geocolname in colmap[col.name]:
                    geocol = geo.column[geocolname]
                    nodez = colnodez(geocol)
                    minnodez = min(nodez)
                    if geocol_min is None: geocol_min = minnodez
                    else: geocol_min = min(geocol_min, minnodez)
                column_values.append(geocol_min)
            else:
                geocol_area, geocol_values = [], []
                for geocolname in colmap[col.name]:
                    geocol = geo.column[geocolname]
                    nodez = colnodez(geocol)
                    geocol_area.append(geocol.area)
                    geocol_values.append(sum(nodez) / geocol.num_nodes)
                val = sum([area * val for area, val in
                           zip(geocol_area, geocol_values)]) / sum(geocol_area)
                column_values.append(val)
        if output_dict:
            return dict(zip([col.name for col in columns], column_values))
        else: return np.array(column_values)

    def fit_surface(self, data, alpha = 0.1, beta = 0.1, columns = [],
                    min_columns = [], grid_boundary = False,
                    layer_snap = 0.0, silent = False):
        """Fits column surface elevations to the grid from the data, using the
        fit_columns() method (see documentation for that method for
        more detail). The layer_snap parameter can be specified as a
        positive number to avoid the creation of very thin top surface
        layers, if the fitted elevation is very close to the bottom of
        a layer.  In this case the value of layer_snap is a tolerance
        representing the smallest permissible layer thickness.
        """

        if columns == []: columns = self.columnlist
        else:
            if isinstance(columns[0], str):
                columns = [self.column[col] for col in columns]

        col_elevations = self.fit_columns(data, alpha, beta, columns,
                                          min_columns, grid_boundary, silent)

        for col, elev in zip(columns, col_elevations):
            col.surface = elev
            self.set_column_num_layers(col)

        self.snap_columns_to_layers(layer_snap, columns)
        self.setup_block_name_index()
        self.setup_block_connection_name_index()



    def from_amesh(self, input_filename = 'in', segment_filename = 'segmt',
              convention = 0, node_tolerance = None,
                   justify = 'r', chars = ascii_lowercase, spaces = True,
                   block_order = None):
        """Reads in AMESH input and segment files for a Voronoi mesh and
        returns a corresponding mulgrid object and block mapping. The
        block mapping dictionary maps block names in the geometry to
        block names in the AMESH grid. The atmosphere type is assumed
        to be 2 (no atmosphere blocks)."""

        from scipy.spatial import cKDTree
        thickness_tol = 1.e-3

        def parse_layers(filename):
            """Parse AMESH input to identify layer structure."""
            with open(filename, 'r') as f:
                found_locat = False
                for line in f:
                    found_locat = line[:5].lower() == 'locat'
                    if found_locat: break
                if not found_locat:
                    raise Exception('Could not find locat block in AMESH input file: ' +
                                    input_filename)
                layers = {}
                for line in f:
                    if line.strip():
                        blkname = line[:5]
                        vals = line[5:].split()
                        index = int(vals[0])
                        x, y, z = float(vals[1]), float(vals[2]), float(vals[3])
                        pos = np.array([x, y])
                        thickness = float(vals[4])
                        if index in layers:
                            layers[index]['block_name'].append(blkname)
                            layers[index]['column_centre'][blkname] = pos
                            thickness_diff = thickness - layers[index]['thickness']
                            thickness_err = thickness_diff / layers[index]['thickness']
                            if abs(thickness_err) > thickness_tol:
                                raise Exception('Non-constant thickness ' +
                                                'for layer containing block: ' + blkname)
                        else:
                            layers[index] = {'block_name': [blkname],
                                             'column_centre': {blkname: pos},
                                             'thickness': thickness,
                                             'elevation': z}
                    else: break
            layer_names = list(layers.keys())
            elevations = np.array([layers[name]['elevation'] for name in layer_names])
            isort = np.argsort(elevations)[::-1]
            layers = [layers[layer_names[i]] for i in isort]
            return layers

        def parse_segments(filename, bottom_layer):
            """Parse AMESH segment file and return list of 2-D segments, together
            with the minimum segment length."""
            segment_data = []
            min_segment_length = sys.float_info.max
            with open(filename) as f:
                for line in f:
                    x1, y1, x2, y2 = float(line[0: 15]), float(line[15: 30]), \
                                     float(line[30: 45]), float(line[45: 60])
                    points = (np.array([x1, y1]), np.array([x2, y2]))
                    idx = int(line[60: 63])
                    blocknames = (line[65: 70], line[70: 75])
                    if all([blkname in bottom_layer['block_name'] or blkname.startswith('*')
                            for blkname in blocknames]):
                        segment_data.append({'points': points,
                                             'index': idx, 'blocknames': blocknames})
                        min_segment_length = min(min_segment_length,
                                                 np.linalg.norm(points[0] - points[1]))
            return segment_data, min_segment_length

        layers = parse_layers(input_filename)
        bottom_layer = layers[-1]
        segment_data, min_segment_length = parse_segments(segment_filename, bottom_layer)

        justfn = [str.rjust, str.ljust][justify == 'l']
        geo = mulgridSubVoronoiAmesh(convention = convention, atmos_type = 2, block_order = block_order)

        # Add nodes:
        nodeindex = 1
        segments = {}
        for blkname in bottom_layer['block_name']: segments[blkname] = []
        if node_tolerance is None: node_tolerance = 0.9 * min_segment_length
        for seg in segment_data:
            nodes = []
            for point in seg['points']:
                new = True
                if geo.num_nodes > 1:
                    kdt = cKDTree([n.pos for n in geo.nodelist])
                    r,i = kdt.query(point)
                    if r < node_tolerance:
                        nodes.append(geo.nodelist[i]) # existing node
                        new = False
                if new: # new node
                    name = geo.node_name_from_number(nodeindex, justfn, chars, spaces)
                    newnode = node(name, point)
                    geo.add_node(newnode)
                    nodes.append(newnode)
                    nodeindex += 1
            for iname, blockname in enumerate(seg['blocknames']):
                if not blockname.startswith('*'):
                    segnodes = nodes if iname == 0 else nodes[::-1]
                    if segnodes not in segments[blockname]:
                        segments[blockname].append(segnodes)

        # Add columns:
        colindex = 1
        for blockname in bottom_layer['block_name']:
            segs = segments[blockname]
            if segs:
                colnodes = segs[0]
                done = False
                while not done:
                    nextsegs = [seg for seg in segs if seg[0] == colnodes[-1]]
                    try:
                        nextseg = nextsegs[0]
                        if nextseg[-1] == colnodes[0]: done = True
                        else: colnodes.append(nextseg[-1])
                    except: raise Exception(
                            "Could not identify column nodes for block:" + blockname)
                colname = geo.column_name_from_number(colindex, justfn, chars, spaces)
                colindex += 1
                pos = bottom_layer['column_centre'][blockname]
                geo.add_column(column(colname, colnodes, pos))
            else: raise Exception(
                    "No line segments found for block: " + blockname)
        # Add layers:
        top_elevation = layers[0]['elevation'] + 0.5 * layers[0]['thickness']
        geo.add_layers([lay['thickness'] for lay in layers], top_elevation,
                       justify, chars, spaces)
        for geolayer, lay in zip(geo.layerlist[1:], layers):
            geolayer.centre = lay['elevation']

        geo.set_default_surface()
        geo.identify_neighbours()
        geo.check(fix = True, silent = True)
        geo.setup_block_name_index()
        geo.setup_block_connection_name_index()

        # compute block mapping:
        orig_block_names = []
        orig_centres = []
        for lay in layers:
            orig_block_names += lay['block_name']
            for blkname in lay['block_name']:
                pos = np.hstack((lay['column_centre'][blkname],
                                 np.array([lay['elevation']])))
                orig_centres.append(pos)
        kdt = cKDTree(orig_centres)
        blockmap = {}
        for blkname in geo.block_name_list:
            layname = geo.layer_name(blkname)
            colname = geo.column_name(blkname)
            pos = geo.block_centre(layname, colname)
            r, i = kdt.query(pos)
            blockmap[blkname] = orig_block_names[i]

        return geo, blockmap

