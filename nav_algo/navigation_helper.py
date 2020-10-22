import nav_algo.coordinates as coord
import nav_algo.boat as boat
import math


def newSailingAngle(boat, target):
    """TODO Determines the best angle to sail at.

        The sailboat follows a locally optimal path (maximize vmg while minimizing
        directional changes) until the global optimum is "better" (based on the
        hysterisis factor).

        Returns:
            float: The best angle to sail (in the global coordinate system).

    """

    beating = 10.0  # TODO

    boat_to_target = target.vectorSubtract(boat.getPosition())

    right_angle_max, right_vmg_max = optAngle(boat, target, True)
    left_angle_max, left_vmg_max = optAngle(boat, target, False)

    boat_heading = boat.sensors.velocity.angle()
    hysterisis = 1.0 + (beating / boat_to_target.magnitude())
    sailing_angle = right_angle_max
    if (abs(right_angle_max - boat_heading) <
            abs(left_angle_max - boat_heading) and right_vmg_max * hysterisis <
            left_vmg_max) or (abs(right_angle_max - boat_heading) >=
                              abs(left_angle_max - boat_heading)
                              and left_vmg_max * hysterisis >= right_vmg_max):
        sailing_angle = left_angle_max

    return sailing_angle


def optAngle(boat, target, right):
    """TODO Determines the best angle to sail on either side of the wind.

        The "best angle" maximizes the velocity made good toward the target.

        Args:
            right (bool): True if evaluating the right side of the wind, False for left.

        Returns:
            float: The best angle to sail (in the global coordinate system).
            float: The velocity made good at the best angle.

    """
    delta_alpha = 1.0  # TODO is this ok?
    alpha = 0.0
    best_vmg = 0.0
    wind_angle = boat.sensors.wind_direction
    best_angle = wind_angle
    boat_to_target = target.vectorSubtract(boat.getPosition())

    while alpha < 180:
        vel = polar(alpha if right else -1.0 * alpha, boat)
        vmg = vel.dot(boat_to_target.toUnitVector())

        if vmg > best_vmg:
            best_vmg = vmg
            best_angle = wind_angle + alpha if right else wind_angle - alpha

        alpha = alpha + delta_alpha

    return coord.rangeAngle(best_angle), best_vmg


def polar(angle, boat):
    """Evaluates the polar diagram for a given angle relative to the wind.

        Args:
            angle (float): A potential boat heading relative to the absolute wind direction.
            boat (BoatController): The BoatController (either sim or real)

        Returns:
            Vector: A unit boat velocity vector in the global coordinate system.

      """
    # TODO might want to use a less simplistic polar diagram
    angle = coord.rangeAngle(angle)
    if (angle > 20 and angle < 160) or (angle > 200 and angle < 340):
        # put back into global coords
        return coord.Vector(angle=angle + boat.sensors.wind_direction)
    return coord.Vector.zeroVector()


def endurance():
    pass


def stationKeeping(boat_controller, waypoints, circle_radius, state):
    if state == "ENTRY":
        stationKeepingWaypoints = []  #Necessary waypoints
        # entry point to the square
        square_entry = waypoints[0].midpoint(waypoints[1])
        stationKeepingWaypoints.append(square_entry)
        # center of the sqaure
        center = waypoints[0].midpoint(waypoints[2])
        stationKeepingWaypoints.append(center)
        waypoints = stationKeepingWaypoints
        return
    elif state == "KEEP":
        # calculate the waypoints in the circle
        x_coord = boat_controller.getPosition().x
        y_coord = boat_controller.getPosition().y
        pos = circle_radius * math.sqrt(2) / 2
        way45 = ((pos) + x_coord, (pos) + y_coord)
        way135 = (-(pos) + x_coord, (pos) + y_coord)
        way225 = (-(pos) + x_coord, -(pos) + y_coord)
        way315 = ((pos) + x_coord, -(pos) + y_coord)
        circle_waypoints = [way45, way135, way225, way315]
        # x//45: check distance to 1 and 7 and take the smaller one for each angle
        # TODO x is a tuple...
        # circle_waypoints = sorted(circle_waypoints,
        #                           key=lambda x: min(abs(
        #                               (x / 45) - 7), abs((x / 45) - 1)))
        # # x % 45: check value and take smaller value
        # circle_waypoints = sorted(circle_waypoints, lambda x: x % 45)
        waypoints = circle_waypoints
        return
    elif state == "EXIT":
        # corner waypoint order: NW, NE, SE, SW
        # TODO: ask Courtney about the units of x-y coord
        units_away = 10
        # north exit
        north_exit = waypoints[0].midpoint(waypoints[1])
        north_exit.y += units_away
        # east exit
        east_exit = waypoints[1].midpoint(waypoints[2])
        east_exit.x += units_away
        #south exit
        south_exit = waypoints[2].midpoint(waypoints[3])
        south_exit.y -= units_away
        #west exit
        west_exit = waypoints[0].midpoint(waypoints[3])
        west_exit.x -= units_away
        # exit waypoint order in list: N, E, S, W
        curr_pos = boat_controller.getPosition()
        shortest_dist = min((curr_pos.xyDist(north_exit), north_exit),
                            (curr_pos.xyDist(east_exit), east_exit),
                            (curr_pos.xyDist(south_exit), south_exit),
                            (curr_pos.xyDist(west_exit), west_exit),
                            key=lambda x: x[0])
        waypoints = [shortest_dist[1]]
        return


def precisionNavigation():
    pass


def collisionAvoidance():
    pass


def search():
    pass
