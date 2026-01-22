"""
SMA Battery Command Generator
Generates command sequences (NOD, DIS, ACC) for SMA battery inverters
based on optimization results.

Commands:
- NOD: No Discharge - Battery can charge from solar but not from grid, no discharge allowed
- DIS: Discharge - Battery discharge is allowed/active
- ACC: Accumulate - Battery charging from grid is allowed/active
"""

def generate_commands(interval, is_discharging_list, battery_discharge_list, 
                     is_charging_list, outside_to_battery_list, solar_to_battery_list):
    """
    Generate SMA battery commands based on optimization results.
    
    Args:
        interval: List of time periods
        is_discharging_list: Binary list indicating discharge state
        battery_discharge_list: List of discharge energy values
        is_charging_list: Binary list indicating charging state
        outside_to_battery_list: List of grid-to-battery energy values
        solar_to_battery_list: List of solar-to-battery energy values
    
    Returns:
        dict: Dictionary mapping time periods to commands
    """
    commands = {}
    
    for i in interval:
        # Battery is discharging
        if is_discharging_list[i] == 1 and battery_discharge_list[i] > 0:
            commands[i] = "DIS"
        
        # Grid energy is used to charge the battery
        elif outside_to_battery_list[i] > 0 and is_charging_list[i] == 1:
            commands[i] = "ACC"
        
        # Only solar charging, no grid charging
        elif (is_discharging_list[i] == 0 and is_charging_list[i] == 1 and 
              outside_to_battery_list[i] == 0 and solar_to_battery_list[i] > 0):
            commands[i] = "NOD"
        
        # No charging or discharging
        elif is_discharging_list[i] == 0 and is_charging_list[i] == 0:
            commands[i] = "NOD"
        
        # Discharge enabled but no actual discharge
        elif is_discharging_list[i] == 1 and battery_discharge_list[i] == 0:
            commands[i] = "NOD"
        
        else:
            commands[i] = "Failure"
    
    return commands

def group_commands(commands):
    """
    Group consecutive identical commands into time intervals.
    
    Args:
        commands: Dictionary mapping time periods to command strings
    
    Returns:
        list: List of dictionaries with 'cmd', 'p1' (start), 'p2' (end)
              Intervals are half-open [p1, p2), meaning p1 is inclusive, p2 is exclusive
    
    Example:
        Input:  {0: 'NOD', 1: 'DIS', 2: 'ACC', 3: 'ACC'}
        Output: [
            {'cmd': 'NOD', 'p1': 0, 'p2': 1},
            {'cmd': 'DIS', 'p1': 1, 'p2': 2},
            {'cmd': 'ACC', 'p1': 2, 'p2': 4}
        ]
    """
    grouped_commands = []
    sorted_intervals = sorted(commands.keys())
    
    if not sorted_intervals:
        return grouped_commands
    
    current_cmd = commands[sorted_intervals[0]]
    start = sorted_intervals[0]
    
    for i in sorted_intervals[1:]:
        if commands[i] != current_cmd:
            grouped_commands.append({
                'cmd': current_cmd,
                'p1': start,
                'p2': i  # i is the first period with new command
            })
            current_cmd = commands[i]
            start = i
    
    # Add last interval
    grouped_commands.append({
        'cmd': current_cmd,
        'p1': start,
        'p2': sorted_intervals[-1] + 1  # +1 for exclusive end
    })
    
    return grouped_commands

def format_command_schedule(grouped_commands, period_duration_minutes=15):
    """
    Format grouped commands into a human-readable schedule.
    
    Args:
        grouped_commands: Output from group_commands()
        period_duration_minutes: Duration of each period in minutes
    
    Returns:
        str: Formatted schedule as string
    """
    schedule = "SMA Battery Command Schedule\n"
    schedule += "=" * 50 + "\n"
    
    for cmd_group in grouped_commands:
        start_time = cmd_group['p1'] * period_duration_minutes
        end_time = cmd_group['p2'] * period_duration_minutes
        start_hours = start_time // 60
        start_mins = start_time % 60
        end_hours = end_time // 60
        end_mins = end_time % 60
        
        schedule += f"{cmd_group['cmd']:3s}  |  "
        schedule += f"Period {cmd_group['p1']:3d} -{cmd_group['p2']:3d}  |  "
        schedule += f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}\n"
    
    return schedule