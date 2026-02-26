"""
geometry_utils.py
Shared geometry functions used across multiple proof scripts.

No dependencies beyond stdlib.
"""

import math


def tang(angle_deg, R):
    """Distance from corner vertex to arc tangent point along each edge."""
    return R / math.tan(math.radians(angle_deg / 2))


def centre_offset(angle_deg, R):
    """Distance from corner vertex to arc centre along inward bisector."""
    return R / math.sin(math.radians(angle_deg / 2))


def inward_bisector(edge_a_dir, edge_b_dir):
    """
    Inward bisector direction at a corner vertex.
    edge_a_dir: direction the arriving edge is travelling (TOWARD vertex).
    edge_b_dir: direction the departing edge is travelling (AWAY from vertex).
    Returns normalised (bx, by).
    Formula: normalise((-edge_a_dir) + edge_b_dir)
    """
    bx = -edge_a_dir[0] + edge_b_dir[0]
    by = -edge_a_dir[1] + edge_b_dir[1]
    mag = math.sqrt(bx*bx + by*by)
    return bx/mag, by/mag


def corner_arc_start_end(vertex, edge_a_dir, edge_b_dir, radius, corner_angle_deg):
    """
    Compute arc start and end points for a corner of given angle.
    Arc start is on edge_a (arriving), arc end is on edge_b (departing).
    Both points are tangent_distance from vertex along their respective edges.
    """
    td = tang(corner_angle_deg, radius)
    arc_start = (vertex[0] - edge_a_dir[0]*td, vertex[1] - edge_a_dir[1]*td)
    arc_end   = (vertex[0] + edge_b_dir[0]*td, vertex[1] + edge_b_dir[1]*td)
    return arc_start, arc_end


def finger_count_and_width(available, nominal):
    """
    Compute odd finger count and adjusted width for a given available length.
    Count = nearest odd integer to (available / nominal_width), minimum 3.
    Actual width = available / count.
    """
    n = round(available / nominal)
    if n % 2 == 0:
        n -= 1
    n = max(3, n)
    return n, available / n


def finger_positions(term_start, count, fw):
    """
    Global positions of each finger (tab or slot) along the edge.
    Returns list of (start, end, is_tab). First finger is a TAB.
    """
    return [(term_start + i*fw, term_start + (i+1)*fw, i % 2 == 0)
            for i in range(count)]
