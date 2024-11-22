import math
from enum import Enum
from time import time
from typing import Optional

import bridge.router.waypoint as wp
from bridge import const
from bridge.auxiliary import aux, fld, rbt
from bridge.processors.referee_state_processor import Color as ActiveTeam
from bridge.processors.referee_state_processor import State as GameStates

ball_start = None

class Strategy:
    """Основной класс с кодом стратегии"""

    def __init__(self, dbg_game_status: GameStates = GameStates.RUN) -> None:
        self.game_status = dbg_game_status
        self.target_point = aux.Point(100, 100)
        self.current = 0
        self.robot_with_ball: Optional[rbt.Robot] = None

        # Индексы роботов
        self.gk_idx = 0
        self.idx1 = 1
        self.idx2 = 2
        # Индексы роботов соперника
        self.gk_idx_ali = 11
        self.idx_ali1 = 3
        self.idx_ali2 = 8

    def change_game_state(self, new_state: GameStates, upd_active_team: ActiveTeam) -> None:
        """Изменение состояния игры и цвета команды"""
        self.game_status = new_state
        self.active_team = upd_active_team

    def is_ball_moves_to_point(self, robot_pos1: aux.Point, ball) -> bool:
        """Определить, движется ли мяч в сторону точки"""
        vec_to_point = robot_pos1 - ball.get_pos()
        return (
            ball.get_vel().mag() * (math.cos(vec_to_point.arg() - ball.get_vel().arg()) ** 5)
            > const.INTERCEPT_SPEED * 5
            and self.robot_with_ball is None
            and abs(vec_to_point.arg() - ball.get_vel().arg()) < math.pi / 2
        )

    def process(self, field: fld.Field) -> list[wp.Waypoint]:
        """Рассчитать конечные точки для каждого робота"""
        waypoints: list[wp.Waypoint] = []
        for i in range(const.TEAM_ROBOTS_MAX_COUNT):
            waypoints.append(
                wp.Waypoint(
                    field.allies[i].get_pos(),
                    field.allies[i].get_angle(),
                    wp.WType.S_STOP,
                )
            )
        
        self.protection(field,waypoints, self.idx2)
        self.attacker(field, waypoints, self.idx1)
        self.goalkeeper(field, waypoints)

        return waypoints

    def attacker(self, field: fld.Field, waypoints: list[wp.Waypoint], idx: int) -> None:
        ##########################coordinates_our##########################
        robot_pos_gk = field.allies[self.gk_idx].get_pos()
        robot_pos1 = field.allies[self.idx1].get_pos()
        robot_pos2 = field.allies[self.idx2].get_pos()

        ##########################coordinates_ali##########################
        robot_pos_gk_ali = field.allies[self.gk_idx_ali].get_pos()
        robot_pos1_ali = field.allies[self.idx_ali1].get_pos()
        robot_pos2_ali = field.allies[self.idx_ali2].get_pos()

        ##########################ball##########################
        ball = field.ball.get_pos()

        ##########################attacker##########################
        g_up_xy = field.ally_goal.up + field.ally_goal.eye_up * 50
        g_down_xy = field.ally_goal.down - field.ally_goal.eye_up * 50
        up = (g_up_xy - robot_pos_gk).mag()
        down = (g_down_xy - robot_pos_gk).mag()

        vec_rob = ((robot_pos_gk + robot_pos2) / 2) - robot_pos1

        if up > down:
            pos = g_up_xy
        else:
            pos = g_down_xy

        angl_atacker = (pos - vec_rob) - robot_pos1
        angl = robot_pos1 - pos
        pos_gool = field.ally_goal.center

        # Ensure vec_ball is always defined
        vec_ball = ball - robot_pos1

        #if vec_ball.mag() > 300:
        #    waypoints[self.idx1] = wp.Waypoint(ball, vec_ball.arg(), wp.WType.S_ENDPOINT)
        #else:
        waypoints[self.idx1] = wp.Waypoint(ball, (angl_atacker).arg(), wp.WType.S_BALL_KICK)

        # Pas
        # if self.is_ball_moves_to_point(robot_pos1, field.ball):
        #    waypoints[self.idx1] = wp.Waypoint(robot_pos1, (vec_ball).arg(), wp.WType.S_ENDPOINT)
        # else:
        #    waypoints[self.idx1] = wp.Waypoint(robot_pos1, (vec_ball).arg(), wp.WType.S_ENDPOINT)
        return waypoints

    def protection(self, field: fld.Field, waypoints: list[wp.Waypoint], idx: int) -> None:
        """##########################coordinates_our##########################
        robot_pos_gk = field.allies[self.gk_idx].get_pos()
        robot_pos1 = field.allies[self.idx1].get_pos()
        robot_pos2 = field.allies[self.idx2].get_pos()

        ##########################coordinates_ali##########################
        robot_pos_gk_ali = field.allies[self.gk_idx_ali].get_pos()
        robot_pos1_ali = field.allies[self.idx_ali1].get_pos()
        robot_pos2_ali = field.allies[self.idx_ali2].get_pos()

        ##########################ball##########################
        ball = field.ball.get_pos()
        
        ##########################protection##########################   

        ball = field.ball.get_pos()
        robot_pos1 = field.allies[idx].get_pos()
        robot_pos2 = field.allies[self.idx2].get_pos()

        angle_protection = robot_pos1 - robot_pos2

        if ball.y > 0:
            waypoints[self.idx2] = wp.Waypoint(ball, (angle_protection).arg(), wp.WType.S_BALL_KICK)
        else:
            waypoints[self.idx2] = wp.Waypoint(ball, (field.enemy_goal.center).arg(), wp.WType.S_BALL_KICK)

        return waypoints"""
    def goalkeeper(self, field: fld.Field, waypoints: list[wp.Waypoint]) -> None:
        """##########################coordinates_our##########################
        robot_pos_gk = field.allies[self.gk_idx].get_pos()

        ##########################ball##########################
        ball = field.ball.get_pos()

        # Define the goal area (assuming it's a rectangle or polygon)
        goal_area = field.ally_goal.hull

        # Calculate the point on the goal line that is closest to the ball
        pos_goal = aux.closest_point_on_line(field.ally_goal.left_post, field.ally_goal.right_post, ball)

        # Ensure the goalkeeper stays within the goal area
        if not aux.is_point_inside_poly(pos_goal, goal_area):
            pos_goal = field.ally_goal.center

        # Calculate the angle towards the ball
        angle_goalkeeper = (ball - robot_pos_gk).arg()

        # Set the waypoint for the goalkeeper to follow the ball
        waypoints[self.gk_idx] = wp.Waypoint(pos_goal, angle_goalkeeper, wp.WType.S_ENDPOINT)

        # If the ball is within the goal area, move the goalkeeper to the ball and kick it away
        if aux.is_point_inside_poly(ball, goal_area):
            waypoints[self.gk_idx] = wp.Waypoint(ball, angle_goalkeeper, wp.WType.S_BALL_KICK)
            print("Kicking the ball away")

        return waypoints"""

