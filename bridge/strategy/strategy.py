"""Верхнеуровневый код стратегии"""

# pylint: disable=redefined-outer-name

# @package Strategy
# Расчет требуемых положений роботов исходя из ситуации на поле


import math

# !v DEBUG ONLY
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

    def __init__(
        self,
        dbg_game_status: GameStates = GameStates.RUN,
    ) -> None:

        self.game_status = dbg_game_status
        self.target_point = aux.Point(100, 100)
        self.current = 0
        self.robot_with_ball: Optional[rbt.Robot] = None

        ##########################idx##########################
        self.gk_idx = 1
        self.idx1 = 8
        self.idx2 = 11

        ##########################idx_al##########################
        self.gk_idx_ali = 11
        self.idx_ali1 = 3
        self.idx_ali2 = 8

    def change_game_state(self, new_state: GameStates, upd_active_team: ActiveTeam) -> None:
        """Изменение состояния игры и цвета команды"""
        self.game_status = new_state
        self.active_team = upd_active_team
    def is_ball_moves_to_point(self, robot_pos1: aux.Point, ball) -> bool:
        """
        Определить, движется ли мяч в сторону точки
        """
        vec_to_point = robot_pos1 - ball.get_pos()
        return (
            ball.get_vel().mag() * (math.cos(vec_to_point.arg() - ball.get_vel().arg()) ** 5)
            > const.INTERCEPT_SPEED * 5
            and self.robot_with_ball is None
            and abs(vec_to_point.arg() - ball.get_vel().arg()) < math.pi / 2
    )
        

    def process(self, field: fld.Field) -> list[wp.Waypoint]:
        """
        Рассчитать конечные точки для каждого робота
        """
        waypoints: list[wp.Waypoint] = []
        for i in range(const.TEAM_ROBOTS_MAX_COUNT):
            waypoints.append(
                wp.Waypoint(
                    field.allies[i].get_pos(),
                    field.allies[i].get_angle(),
                    wp.WType.S_STOP,
                )
            )
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
        #if (self.target_point - robot_pos).mag() < 100:
        #    self.current = (self.current + 1) % len(pos_points)
        #    self.target_point = pos_points[self.current]

        g_up_xy = field.ally_goal.up + field.ally_goal.eye_up * 50 
        g_down_xy = field.ally_goal.down - field.ally_goal.eye_up * 50 
        up = (g_up_xy - robot_pos1).arg()
        down = (robot_pos1 - g_down_xy).arg()

        vec_rob = ((robot_pos_gk + robot_pos2) / 2) - robot_pos1

        if up > down:
            pos = g_up_xy
        else:
            pos = g_down_xy
        
        
        angl_atacker = (pos - vec_rob) - robot_pos1  
        angl = robot_pos1 - pos
        pos_gool = field.ally_goal.center
    
        vec_ball = ball - robot_pos1
        #if vec_ball.mag() > 300:
        #    waypoints[self.idx1] = wp.Waypoint(ball, vec_ball.arg(), wp.WType.S_ENDPOINT)
        #else:
        #    waypoints[self.idx1] = wp.Waypoint(ball, (angl_atacker).arg(), wp.WType.S_BALL_KICK)
        
        if self.is_ball_moves_to_point(robot_pos1, field.ball):
            waypoints[self.idx1] = wp.Waypoint(robot_pos1, (vec_ball).arg(), wp.WType.S_ENDPOINT)
        return waypoints


        #waypoints[self.idx1] = wp.Waypoint(ball, angl_atacker.arg(), wp.WType.S_BALL_KICK)

        ##########################protection##########################
        #angle_protection = robot_pos1 - robot_pos2
        #waypoints[self.idx2] = wp.Waypoint(ball, (angle_protection).arg(), wp.WType.S_BALL_PASS)

        
        ##########################goalkeper##########################
        if ball_start is not None:
            pos_goal = aux.closest_point_on_line(ball_start, ball, robot_pos_gk, "R")
        else:
            pos_goal = field.ally_goal.center   
        pos_g = aux.is_point_inside_poly(pos_goal, field.ally_goal.hull)

        if pos_g == False:
            pos_goal = field.ally_goal.center

        angle_golkeper = (ball - robot_pos_gk).arg()

        waypoints[self.gk_idx] = wp.Waypoint(pos_goal, angle_golkeper, wp.WType.S_ENDPOINT)

        if field.is_ball_stop_near_goal(): 
            waypoints[self.gk_idx] = wp.Waypoint(ball, angle_golkeper, wp.WType.S_BALL_KICK)
        print(1)
        if field.is_ball_in(field.allies[self.gk_idx]):            
            waypoints[self.gk_idx] = wp.Waypoint(pos_goal, angle_golkeper, wp.WType.S_BALL_KICK)    
            print(2)
            waypoints[self.gk_idx] = wp.Waypoint(pos_goal, angle_golkeper, wp.WType.S_ENDPOINT)
        return waypoints
