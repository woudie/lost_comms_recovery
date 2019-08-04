#!/usr/bin/env python
import sys
import time
import rospy
import subprocess

from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist


def ping_host(host):
  ping_fail_count = rospy.get_param('~ping_fail_count', 2)
  ping_command = "ping -c %s -n -W 1 %s" % (ping_fail_count, host)
  # TODO: don't shell out, use a more secure python library
  p = subprocess.Popen(ping_command,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True)
  (output, error) = p.communicate()
  returncode = p.returncode
  return output, error, returncode

class RecorveryController():
  def __init__(self):
    self.drive_publisher = rospy.Publisher('cmd_vel', Twist, queue_size=10)
    self.arm_publisher = rospy.Publisher('arm_mux', Float32MultiArray, queue_size=10)

  def working_comms(self):
    working_comms = False
    for ip in self.ips.split(','):
      (output, error, returncode) = ping_host(ip)
      if returncode == 0:
        working_comms = True
    return working_comms

  def zero_arm(self):
    rospy.loginfo('Zeroing joystick.')
    arm = Float32MultiArray()
    arm.data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # Set all motors to zero
    self.arm_publisher.publish(arm)

  def zero_drive(self):
    rospy.loginfo('Stopping motors.')
    twist = Twist() # zero motion
    self.drive_publisher.publish(twist)
    
  def do_recovery(self):
    if rospy.is_shutdown(): return
    rospy.logerr('No connection to base station.')
    self.zero_arm()
    self.zero_drive()

  def main_loop(self):
    while not rospy.is_shutdown():
      if not self.working_comms():
        self.do_recovery()
      else:
        rospy.loginfo('Connected to base station.')
      time.sleep(3)


def main():
  rospy.init_node("lost_comms_recovery")
  Controller = RecorveryController()
  Controller.ips = rospy.get_param('~ips_to_monitor')
  rospy.loginfo('Monitoring base station on IP(s): %s.' % Controller.ips)
  Controller.main_loop() # start monitoring
