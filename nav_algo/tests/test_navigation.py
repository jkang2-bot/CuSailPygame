import unittest
import numpy as np
import nav_algo.navigation as nav
import nav_algo.coordinates as coord
from nav_algo.navigation_helper import *


class TestNavigationMethods(unittest.TestCase):
    def setUp(self):
        self.waypoints = [(42.444241, 76.481933), (42.446016, 76.484713)]
        self.nav_controller = nav.NavigationController(
            waypoints=self.waypoints, test=True)

        # mock sensor readings - some of these aren't always used
        self.nav_controller.boat.sensors.wind_direction = 45.0
        self.nav_controller.boat.sensors.fix = True
        self.nav_controller.boat.sensors.position = coord.Vector(x=5.0, y=0.0)
        self.nav_controller.boat.sensors.velocity = coord.Vector(x=0.3, y=0.4)

    def test_polar(self):
        # directly upwind
        v = polar(0.0, self.nav_controller.boat)
        self.assertAlmostEqual(v.x, 0.0)
        self.assertAlmostEqual(v.y, 0.0)

        # directly downwind
        v = polar(180.0, self.nav_controller.boat)
        self.assertAlmostEqual(v.x, 0.0)
        self.assertAlmostEqual(v.y, 0.0)

        # port
        v = polar(270.0, self.nav_controller.boat)
        self.assertAlmostEqual(v.magnitude(), 1.0)
        self.assertAlmostEqual(
            v.angle(), 270.0 + self.nav_controller.boat.sensors.wind_direction)

        # starboard
        v = polar(30.0, self.nav_controller.boat)
        self.assertAlmostEqual(v.magnitude(), 1.0)
        self.assertAlmostEqual(
            v.angle(), 30.0 + self.nav_controller.boat.sensors.wind_direction)

    def test_optAngle(self):
        # best angle is directly to target on the left side
        self.nav_controller.boat.sensors.position = coord.Vector(x=-1.0, y=0.0)
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              False)  # left side
        self.assertAlmostEqual(angle, 0.0)
        self.assertAlmostEqual(vmg, 1.0)
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              True)  # right side
        self.assertAlmostEqual(angle, 66.0)
        self.assertAlmostEqual(vmg, np.cos(coord.degToRad(66.0)))

        # best angle is directly to target on the right side
        self.nav_controller.boat.sensors.position = coord.Vector(x=1.0, y=0.0)
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              True)  # right side
        self.assertAlmostEqual(angle, 180.0)
        self.assertAlmostEqual(vmg, 1.0)
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              False)  # left side
        self.assertAlmostEqual(angle, 246.0)
        self.assertAlmostEqual(vmg, -1.0 * np.cos(coord.degToRad(246.0)))

        # target is directly upwind (get as close as possible)
        self.nav_controller.boat.sensors.position = coord.Vector(x=-1.0,
                                                                 y=-1.0)
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              True)  # right side
        self.assertAlmostEqual(angle, 66.0)
        self.assertAlmostEqual(
            vmg,
            np.sin(coord.degToRad(66.0)) * np.sin(coord.degToRad(45.0)) +
            np.cos(coord.degToRad(66.0)) * np.cos(coord.degToRad(45.0)))
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              False)  # left side
        self.assertAlmostEqual(angle, 24.0)
        self.assertAlmostEqual(
            vmg,
            np.sin(coord.degToRad(24.0)) * np.sin(coord.degToRad(45.0)) +
            np.cos(coord.degToRad(24.0)) * np.cos(coord.degToRad(45.0)))

        # target is directly downwind (get as close as possible)
        self.nav_controller.boat.sensors.position = coord.Vector(x=1.0, y=1.0)
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              True)  # right side
        self.assertAlmostEqual(angle, 204.0)
        self.assertAlmostEqual(
            vmg,
            np.sin(coord.degToRad(204.0)) * np.sin(coord.degToRad(225.0)) +
            np.cos(coord.degToRad(204.0)) * np.cos(coord.degToRad(225.0)))
        angle, vmg = optAngle(self.nav_controller.boat,
                              self.nav_controller.current_waypoint,
                              False)  # left side
        self.assertAlmostEqual(angle, 246.0)
        self.assertAlmostEqual(
            vmg,
            np.sin(coord.degToRad(246.0)) * np.sin(coord.degToRad(225.0)) +
            np.cos(coord.degToRad(246.0)) * np.cos(coord.degToRad(225.0)))

    def test_newSailingAngle(self):
        # should turn back toward origin on the right
        angle = newSailingAngle(self.nav_controller.boat,
                                self.nav_controller.current_waypoint)
        self.assertAlmostEqual(
            angle,
            self.nav_controller.boat.sensors.position.inverse().angle())

        self.nav_controller.boat.sensors.position = coord.Vector(x=-50.0,
                                                                 y=0.0)
        angle = newSailingAngle(self.nav_controller.boat,
                                self.nav_controller.current_waypoint)
        self.assertAlmostEqual(angle, 0.0)

        # beating
        self.nav_controller.boat.sensors.position = coord.Vector(x=-50.0,
                                                                 y=-50.0)
        angle = newSailingAngle(self.nav_controller.boat,
                                self.nav_controller.current_waypoint)
        self.assertAlmostEqual(angle, 66.0)  # right side is closer to heading

        self.nav_controller.boat.sensors.position = coord.Vector(x=-50.0,
                                                                 y=-50.0)
        self.nav_controller.boat.sensors.velocity = coord.Vector(x=0.4, y=0.3)
        angle = newSailingAngle(self.nav_controller.boat,
                                self.nav_controller.current_waypoint)
        self.assertAlmostEqual(angle, 24.0)  # left side is closer to heading

        # tacking - heading is closer to right, but target is closer to left
        self.nav_controller.boat.sensors.position = coord.Vector(x=-20.0,
                                                                 y=-5.0)
        self.nav_controller.boat.sensors.velocity = coord.Vector(x=0.3, y=0.4)
        angle = newSailingAngle(self.nav_controller.boat,
                                self.nav_controller.current_waypoint)
        self.assertAlmostEqual(angle, 14.0)

        # tacking - heading is closer to left, but target is closer to right
        self.nav_controller.boat.sensors.position = coord.Vector(x=-5.0,
                                                                 y=-20.0)
        self.nav_controller.boat.sensors.velocity = coord.Vector(x=0.4, y=0.3)
        angle = newSailingAngle(self.nav_controller.boat,
                                self.nav_controller.current_waypoint)
        self.assertAlmostEqual(angle, 76.0)


if __name__ == '__main__':
    unittest.main()