--- Date and Date Format classes.
-- @classmod pl.Date
-- @pragma nostrip

local class = require 'pl.class'
local assert_arg,assert_string = utils.assert_arg,utils.assert_string

local Date = class()
Date.Format = class()

  --- Date constructor.
  -- @param t this can be either
  -- @param ...  true if  Universal Coordinated Time, or two to five numbers: month,day,hour,min,sec
  -- @function Date
          function Date:_init(t,...)
  local time
              local nargs = select('#',...)
  if nargs > 2 then
    local extra = {...}
    local year = t
    t = {
      year = year,
      month = extra[1],
      day = extra[2],
      hour = extra[3],
      min = extra[4],
      sec = extra[5]
    }
  end
  if nargs == 1 then
    self.utc = select(1,...) == true
  end
  if t == nil or t == 'utc' then
    time = os_time()
    self.utc = t == 'utc'
  elseif type(t) == 'number' then
    time = t
    if self.utc == nil then self.utc = true end
  elseif type(t) == 'table' then
    if getmetatable(t) == Date then -- copy ctor
      time = t.time
      self.utc = t.utc
    else
    end
  else
    error("bad type for Date constructor: "..type(t),2)
  end
  self:set(time)
      end
