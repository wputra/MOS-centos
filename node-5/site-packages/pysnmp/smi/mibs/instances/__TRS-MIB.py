import time

# Import managed objects
( trsDeliveryTime,
  trsMessagesPerHour,
  trsGatewayTable,
  trsGatewayEntry,
  trsGatewayIndex,
  trsGatewayName,
  trsGatewayState, ) = mibBuilder.importSymbols(
  'TRS-MIB',
  'trsDeliveryTime',
  'trsMessagesPerHour',
  'trsGatewayTable',
  'trsGatewayEntry',
  'trsGatewayIndex',
  'trsGatewayName',
  'trsGatewayState', 
  )

# Columnar managed objects instances implementation

class TrsDeliveryTimeInstance(MibScalarInstance):
  def readGet(self, name, val, *args):
    if name[-1] == 0:  # Row #0
      return self.name, self.syntax(int(time.time()))
    elif name[-1] == 1: # Row #1
      return self.name, self.syntax(time.time()//2)
    else:
      MibScalarInstance.readGet(self, name, val, *args)

class TrsMessagesPerHourInstance(MibScalarInstance):
  def readGet(self, name, val, *args):
    if name[-1] == 0: # Row #0
      return self.name, self.syntax(-int(time.time()))
    elif name[-1] == 1: # Row #1
      return self.name, self.syntax(-time.time()//2)
    else:
      MibScalarInstance.readGet(self, name, val, *args)

class TrsGatewayIndexInstance(MibScalarInstance):
  def readGet(self, name, val, *args):
    if name[-1] == 0: # Row #0
      return self.name, self.syntax(0)
    elif name[-1] == 1: # Row #1
      return self.name, self.syntax(1)
    else:
      MibScalarInstance.readGet(self, name, val, *args)

class TrsGatewayNameInstance(MibScalarInstance):
  def readGet(self, name, val, *args):
    if name[-1] == 0: # Row #0
      return self.name, self.syntax('SMG0')
    elif name[-1] == 1: # Row #1
      return self.name, self.syntax('SMG1')
    else:
      MibScalarInstance.readGet(self, name, val, *args)

class TrsGatewayStateInstance(MibScalarInstance):
  def readGet(self, name, val, *args):
    if name[-1] == 0: # Row #0
      return self.name, self.syntax('UP' + str(time.time()))
    elif name[-1] == 1: # Row #1
      return self.name, self.syntax('DOWN' + str(time.time()))
    else:
      MibScalarInstance.readGet(self, name, val, *args)

# Instantiate and export managed objects instances
mibBuilder.exportSymbols(
  "__TRS-MIB",
  # Row #0
  TrsDeliveryTimeInstance(trsDeliveryTime.getName(), 0, trsDeliveryTime.getSyntax()),
  TrsMessagesPerHourInstance(trsMessagesPerHour.getName(), 0, trsMessagesPerHour.getSyntax()),
  TrsGatewayIndexInstance(trsGatewayIndex.getName(), 0, trsGatewayIndex.getSyntax()),
  TrsGatewayNameInstance(trsGatewayName.getName(), 0, trsGatewayName.getSyntax()),
  TrsGatewayStateInstance(trsGatewayState.getName(), 0, trsGatewayState.getSyntax()),
  # Row #1
  TrsDeliveryTimeInstance(trsDeliveryTime.getName(), 1, trsDeliveryTime.getSyntax()),
  TrsMessagesPerHourInstance(trsMessagesPerHour.getName(), 1, trsMessagesPerHour.getSyntax()),
  TrsGatewayIndexInstance(trsGatewayIndex.getName(), 1, trsGatewayIndex.getSyntax()),
  TrsGatewayNameInstance(trsGatewayName.getName(), 1, trsGatewayName.getSyntax()),
  TrsGatewayStateInstance(trsGatewayState.getName(), 1, trsGatewayState.getSyntax())
)
