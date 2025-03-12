import math
from enum import Enum
from time import time
from typing import Optional

import bridge.router.waypoint as wp
from bridge import const
from bridge.auxiliary import aux, fld, rbt
from bridge.processors.referee_state_processor import Color as ActiveTeam
from bridge.processors.referee_state_processor import State as GameStates

ball_in_robot = None
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
        self.gk_idx_enem = 0
        self.idx_enem1 = 1
        self.idx_enem2 = 2

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
        #print(231)
        self.attacker(field, waypoints, self.idx1)
        self.goalkeeper(field, waypoints, )

        return waypoints

    
    
    def attacker(self, field: fld.Field, waypoints: list[wp.Waypoint], idx: int) -> None:
        ##########################coordinates_our##########################
        robot_pos_gk = field.allies[self.gk_idx].get_pos()
        robot_pos1 = field.allies[self.idx1].get_pos()
        robot_pos2 = field.allies[self.idx2].get_pos()

        ##########################coordinates_ali##########################
        robot_pos_gk_enem = field.enemies[self.gk_idx_enem].get_pos()
        robot_pos1_enem = field.enemies[self.idx_enem1].get_pos()
        robot_pos2_enem = field.enemies[self.idx_enem2].get_pos()

        ##########################ball##########################
        ball = field.ball.get_pos()

        ##########################attacker##########################
        g_up_xy_attacker = field.enemy_goal.up - field.enemy_goal.eye_up * 0    #определяется угол ворот противоположный от враторя
        g_down_xy_attacker = field.enemy_goal.down + field.enemy_goal.eye_up * 70

        up_attacker = (g_up_xy_attacker - robot_pos_gk_enem).mag()
        down_attacker = (robot_pos_gk_enem + g_down_xy_attacker).mag()


        distance1 = (robot_pos_gk - robot_pos1_enem).mag()
        distamce2 = (robot_pos_gk - robot_pos2_enem).mag()

        attacker_position = ball

        if up_attacker > down_attacker:
            position_attacker_gate = g_up_xy_attacker
        else:
            position_attacker_gate = g_down_xy_attacker     #закончилось

        if distance1 < distamce2:            #смотрится кто дальше находится от враторя  
            if robot_pos2_enem.y > robot_pos1.y:         #находится ли робот относительно мяча с право или слева    
                angle_atacker = position_attacker_gate - robot_pos1
                field.strategy_image.draw_line(robot_pos1, position_attacker_gate, (255, 0, 0), 5)

            else:
                mag = robot_pos2_enem       #бъёт между роботов в противоположный угол
                vector_robot = ((robot_pos_gk_enem + robot_pos2_enem) / 2) - robot_pos1
                angle_atacker = (position_attacker_gate - vector_robot) - robot_pos1
                field.strategy_image.draw_line(robot_pos2_enem, robot_pos_gk_enem, (255, 0, 0), 5)
                field.strategy_image.draw_line(robot_pos1, position_attacker_gate, (0, 0, 255), 5)

        else:
            if robot_pos1_enem.y > robot_pos1.y:     #находится ли робот относительно мяча с право или слева 
                angle_atacker = position_attacker_gate - robot_pos1
                field.strategy_image.draw_line(robot_pos1, position_attacker_gate, (0, 0, 255), 5)

            else:
                mag = robot_pos1_enem       #бъёт между роботов в противоположный угол
                vector_robot = ((robot_pos_gk_enem + robot_pos1_enem) / 2) - robot_pos1
                angle_atacker = (position_attacker_gate - vector_robot) - robot_pos1
                field.strategy_image.draw_line(robot_pos1_enem, robot_pos_gk_enem, (0, 0, 255), 5)
                field.strategy_image.draw_line(robot_pos1, position_attacker_gate, (255, 0, 0), 5)
                #print(1)

        #реализация паса

        #if vec_ball.mag() > 1000:
        #    waypoints[self.idx1] = wp.Waypoint(ball, vec_ball.arg(), wp.WType.S_ENDPOINT)
        #else:
        #waypoints[self.idx1] = wp.Waypoint(ball, angl_atacker.arg(), wp.WType.S_BALL_KICK)

        # if self.is_ball_moves_to_point(robot_pos1, field.ball):
        #    waypoints[self.idx1] = wp.Waypoint(robot_pos1, (vec_ball).arg(), wp.WType.S_ENDPOINT)
        # else:
        #    waypoints[self.idx1] = wp.Waypoint(robot_pos1, (vec_ball).arg(), wp.WType.S_ENDPOINT)

        ###################protection###################

        # Определяем, какой робот ближе к мячу
        ###################защита###################
        ball_in_robot = None
        angle_protection = ball
        protection_position = ball
        
        dist_ball_robot1 = (robot_pos1_enem - ball).mag()
        dist_ball_robot2 = (robot_pos2_enem - ball).mag()
 

        # Используем позицию ближайшего робота
        if dist_ball_robot1 < dist_ball_robot2:
            dist_ball = robot_pos1_enem
        else:
            dist_ball = robot_pos2_enem

        if robot_pos1_enem == ball:
            ball_in_robot = robot_pos1_enem
        elif robot_pos2_enem == ball:
            ball_in_robot = robot_pos2_enem



        g_up_xy_protection = field.ally_goal.up - field.ally_goal.eye_forw * 30    #определяется угол ворот противоположный от враторя
        g_down_xy_protection = field.ally_goal.down + field.ally_goal.eye_forw * 30

        up_protection = (g_up_xy_protection - robot_pos_gk).mag()
        down_protection = (robot_pos_gk - g_down_xy_protection).mag()

        if up_protection < down_protection:
            protection_position_gate = g_up_xy_protection
        else:
            protection_position_gate = g_down_xy_protection

            
        #if ball_in_robot is not None and ball_in_robot.x > 0:
        #    protection_position = aux.Point(pos_ally.x, (field.ally_goal.center).y + 500)
        #    angl_protection = ball_in_robot 

        if dist_ball.x < 0:
            #protection_position = aux.closest_point_on_line(pos_ally, dist_ball, robot_pos2)
            protection_position = aux.Point(dist_ball.x - 300, dist_ball.y)
            angle_protection = (dist_ball - robot_pos2)
        elif dist_ball.x > 0:
            protection_position = aux.closest_point_on_line(protection_position_gate, dist_ball, robot_pos2)
            angle_protection = (dist_ball - robot_pos2)

        elif robot_pos1.x < 0 and robot_pos2.x < 0:
            oblique_robot1 = aux.get_tangent_points(robot_pos1, ball, const.ROBOT_R)
            oblique_robot2 = aux.get_tangent_points(robot_pos2, ball, const.ROBOT_R)
            if len(oblique_robot1) >= 2 and len(oblique_robot2) >= 2:

                field.strategy_image.draw_line(oblique_robot1[0], dist_ball, (255, 0, 0), 5)
                field.strategy_image.draw_line(oblique_robot1[1], dist_ball, (255, 0, 0), 5)

                field.strategy_image.draw_dot(oblique_robot1[0], (255, 0, 0), 50)
                field.strategy_image.draw_dot(oblique_robot1[1], (255, 0, 0), 50)

                field.strategy_image.draw_line(oblique_robot2[0], dist_ball, (255, 0, 0), 5)
                field.strategy_image.draw_line(oblique_robot2[1], dist_ball, (255, 0, 0), 5)

                field.strategy_image.draw_dot(oblique_robot2[0], (255, 0, 0), 50)
                field.strategy_image.draw_dot(oblique_robot2[1], (255, 0, 0), 50)
                angle_protection = dist_ball

            if oblique_robot1[0].distance_to(oblique_robot2[0]) < oblique_robot1[0].distance_to(oblique_robot2[1]):
                protection_position1 = oblique_robot1[1]
                protection_position2 = oblique_robot2[0]
            else:
                protection_position1 = oblique_robot1[0]
                protection_position2 = oblique_robot2[1]


            protection_position_oblique1 = aux.closest_point_on_line(protection_position_gate, robot_pos2_enem, protection_position1)
            protection_position_oblique2 = aux.closest_point_on_line(protection_position_gate, robot_pos2_enem, protection_position2)

            attacker_position = aux.Point(protection_position1.x - 100, protection_position_oblique1.y )
            protection_position = aux.Point(protection_position2.x - 100, protection_position_oblique2.y )

            # Установите ориентации роботов, чтобы они были направлены на мяч
            angle_atacker = (robot_pos2_enem - protection_position1)
            angle_protection = (robot_pos2_enem - protection_position2)


        field.strategy_image.draw_line(dist_ball, protection_position_gate, (0, 0, 255), 5)  

        waypoints[self.idx1] = wp.Waypoint(attacker_position, angle_atacker.arg(), wp.WType.S_BALL_KICK)
        waypoints[self.idx2] = wp.Waypoint(protection_position, angle_protection.arg(), wp.WType.S_ENDPOINT)
        return waypoints


    def goalkeeper(self, field: fld.Field, waypoints: list[wp.Waypoint]) -> None:
        # Получаем позиции союзных роботов
        robot_pos_gk = field.allies[self.gk_idx].get_pos()
        robot_pos1 = field.allies[self.idx1].get_pos()
        robot_pos2 = field.allies[self.idx2].get_pos()
    
        # Получаем позиции вражеских роботов
        robot_pos_gk_enem = field.enemies[self.gk_idx_enem].get_pos()
        robot_pos1_enem = field.enemies[self.idx_enem1].get_pos()
        robot_pos2_enem = field.enemies[self.idx_enem2].get_pos()
    
        # Получаем позицию мяча
        ball = field.ball.get_pos()


        g_up_xy_goal = field.enemy_goal.up - field.enemy_goal.eye_up * 30    #определяется угол ворот противоположный от враторя
        g_down_xy_goal = field.enemy_goal.down + field.enemy_goal.eye_up * 30

        up_goal = (g_up_xy_goal - robot_pos_gk_enem).mag()
        down_goal = (robot_pos_gk_enem + g_down_xy_goal).mag()

        if up_goal > down_goal:
            goal_position_gates = g_up_xy_goal
        else:
            goal_position_gates = g_down_xy_goal     #закончилось

        angle_goal_ball = (goal_position_gates - robot_pos_gk).arg()

    
        # Определяем позицию для вратаря
        if field.ball_start_point is not None:
            goal_position = aux.closest_point_on_line(field.ball_start_point, ball, robot_pos_gk, "R")
        else:
            goal_position = field.ally_goal.center

        position_goal = aux.is_point_inside_poly(goal_position, field.ally_goal.hull)

        if position_goal == False:
            goal_position = field.ally_goal.center

        angle_goalkeeper = (ball - robot_pos_gk).arg()
    
        waypoints[self.gk_idx] = wp.Waypoint(goal_position, angle_goal_ball, wp.WType.S_ENDPOINT)
    
        if field.is_ball_stop_near_goal():
            waypoints[self.gk_idx] = wp.Waypoint(ball, angle_goal_ball, wp.WType.S_BALL_KICK)
    
        if field.is_ball_in(field.allies[self.gk_idx]):
            waypoints[self.gk_idx] = wp.Waypoint(goal_position, angle_goal_ball, wp.WType.S_BALL_KICK)

        #waypoints[self.gk_idx] = wp.Waypoint(goal_position, angle_goalkeeper, wp.WType.S_BALL_KICK)
    
        return None
