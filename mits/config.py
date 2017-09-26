from uber.common import *

config = parse_config(__file__)
c.include_plugin_config(config)

# The number of steps to the MITS application process.  Since changing this requires a code change
# anyway (in order to add another step), this is hard-coded here rather than being a config option.
c.MITS_APPLICATION_STEPS = 6

# The options for the recommended minimum age for games, as filled out by the teams.
c.MITS_AGE_OPTS = [(i, i) for i in range(4, 20, 2)]

# Add the access levels we defined to c.ACCESS* (this will go away if/when we implement enum merging)
c.ACCESS.update(c.MITS_ACCESS_LEVELS)
c.ACCESS_OPTS.extend(c.MITS_ACCESS_LEVEL_OPTS)
c.ACCESS_VARS.extend(c.MITS_ACCESS_LEVEL_VARS)
