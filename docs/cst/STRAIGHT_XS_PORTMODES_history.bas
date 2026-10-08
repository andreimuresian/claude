' define units
With Units
     .SetUnit "Length", "mm"
     .SetUnit "Frequency", "GHz"
     .SetUnit "Voltage", "V"
     .SetUnit "Resistance", "Ohm"
     .SetUnit "Inductance", "nH"
     .SetUnit "Temperature", "degC"
     .SetUnit "Time", "ns"
     .SetUnit "Current", "A"
     .SetUnit "Conductance", "S"
     .SetUnit "Capacitance", "pF"
End With

' define material: LN
With Material
     .Reset
     .Name "LN"
     .Folder ""
     .FrqType "all"
     .Type "Anisotropic"
     .MaterialUnit "Frequency", "GHz"
     .MaterialUnit "Geometry", "mm"
     .EpsilonX "43"
     .EpsilonY "28"
     .EpsilonZ "43"
     .MuX "1"
     .MuY "1"
     .MuZ "1"
     .Colour "0", "0", "0"
     .Create
End With

' define material: SIO2
With Material
     .Reset
     .Name "SIO2"
     .Folder ""
     .FrqType "all"
     .Type "Normal"
     .Epsilon "3.9"
     .Mu "1"
     .Colour "0", "0", "1"
     .Create
End With

' define material: Silicon (lossy)
With Material
     .Reset
     .Name "Silicon (lossy)"
     .Folder ""
     .FrqType "all"
     .Type "Normal"
     .SetMaterialUnit "GHz", "mm"
     .Epsilon "11.9"
     .Mu "1.0"
     .Kappa "2.5e-004"
     .Colour "0.666667", "0.666667", "1"
     .Create
End With

' define material: Gold
With Material
     .Reset
     .Name "Gold"
     .Folder ""
     .FrqType "all"
     .Type "Lossy metal"
     .MaterialUnit "Frequency", "GHz"
     .MaterialUnit "Geometry", "mm"
     .Mu "1.0"
     .Sigma "4.561e+007"
     .Rho "19320.0"
     .Colour "1", "1", "0"
     .Create
End With

' new component: component1
Component.New "component1"

' define brick: component1:si
With Brick
     .Reset
     .Name "si"
     .Component "component1"
     .Material "Silicon (lossy)"
     .Xrange "-0.304975", "-0.004975"
     .Yrange "-0.25", "0.25"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:box
With Brick
     .Reset
     .Name "box"
     .Component "component1"
     .Material "SIO2"
     .Xrange "-0.004975", "-0.000275"
     .Yrange "-0.25", "0.25"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:slab
With Brick
     .Reset
     .Name "slab"
     .Component "component1"
     .Material "LN"
     .Xrange "-0.000275", "0"
     .Yrange "-0.25", "0.25"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:cap
With Brick
     .Reset
     .Name "cap"
     .Component "component1"
     .Material "SIO2"
     .Xrange "0", "0.0036"
     .Yrange "-0.25", "0.25"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:signal
With Brick
     .Reset
     .Name "signal"
     .Component "component1"
     .Material "Gold"
     .Xrange "0.0036", "0.0056"
     .Yrange "-0.0175", "0.0175"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:ground_r
With Brick
     .Reset
     .Name "ground_r"
     .Component "component1"
     .Material "Gold"
     .Xrange "0.0036", "0.0056"
     .Yrange "0.022", "0.07185"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:ground_l
With Brick
     .Reset
     .Name "ground_l"
     .Component "component1"
     .Material "Gold"
     .Xrange "0.0036", "0.0056"
     .Yrange "-0.07185", "-0.022"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:gap_r
With Brick
     .Reset
     .Name "gap_r"
     .Component "component1"
     .Material "Vacuum"
     .Xrange "0.0036", "0.0056"
     .Yrange "0.0175", "0.022"
     .Zrange "0", "0.05"
     .Create
End With

' define brick: component1:gap_l
With Brick
     .Reset
     .Name "gap_l"
     .Component "component1"
     .Material "Vacuum"
     .Xrange "0.0036", "0.0056"
     .Yrange "-0.022", "-0.0175"
     .Zrange "0", "0.05"
     .Create
End With

' create group: meshgroup_xs
Group.Add "meshgroup_xs", "mesh"

' add items to group: meshgroup_xs
Group.AddItem "solid$component1:signal", "meshgroup_xs"
Group.AddItem "solid$component1:ground_r", "meshgroup_xs"
Group.AddItem "solid$component1:ground_l", "meshgroup_xs"
Group.AddItem "solid$component1:gap_r", "meshgroup_xs"
Group.AddItem "solid$component1:gap_l", "meshgroup_xs"

' define frequency range
Solver.FrequencyRange "59.9", "60"

' define background
With Background
     .ResetBackground
     .XminSpace "0.0"
     .XmaxSpace "0.05"
     .YminSpace "0.0"
     .YmaxSpace "0.0"
     .ZminSpace "0.0"
     .ZmaxSpace "0.0"
     .ApplyInAllDirections "False"
End With

' define boundaries
With Boundary
     .Xmin "open"
     .Xmax "open"
     .Ymin "open"
     .Ymax "open"
     .Zmin "open"
     .Zmax "open"
     .Xsymmetry "none"
     .Ysymmetry "none"
     .Zsymmetry "none"
     .ApplyInAllDirections "True"
End With

' set mesh properties (Hexahedral FIT)
With Mesh
     .MeshType "PBA"
     .SetCreator "High Frequency"
End With
With MeshSettings
     .SetMeshType "Hex"
     .Set "Version", 1%
     .Set "StepsPerWaveNear", "50"
     .Set "StepsPerWaveFar", "50"
     .Set "WavelengthRefinementSameAsNear", "1"
     .Set "StepsPerBoxNear", "50"
     .Set "StepsPerBoxFar", "50"
     .Set "MaxStepNear", "0"
     .Set "MaxStepFar", "0"
     .Set "ModelBoxDescrNear", "maxedge"
     .Set "ModelBoxDescrFar", "maxedge"
     .Set "UseMaxStepAbsolute", "0"
     .Set "GeometryRefinementSameAsNear", "1"
     .Set "UseRatioLimitGeometry", "1"
     .Set "RatioLimitGeometry", "50"
     .Set "MinStepGeometryX", "0"
     .Set "MinStepGeometryY", "0"
     .Set "MinStepGeometryZ", "0"
     .Set "UseSameMinStepGeometryXYZ", "1"
End With
With MeshSettings
     .SetMeshType "Hex"
     .Set "EdgeRefinementType", "RATIO"
     .Set "EdgeRefinementRatio", "2"
     .Set "EdgeRefinementStep", "0"
     .Set "EdgeRefinementBufferLines", "3"
     .Set "BufferLinesNear", "3"
     .Set "UseDielectrics", "1"
     .Set "EquilibrateOn", "1"
     .Set "Equilibrate", "1.5"
     .Set "IgnoreThinPanelMaterial", "0"
End With
With Mesh
     .ConnectivityCheck "True"
     .UsePecEdgeModel "True"
End With

' define port: 1
With Port
     .Reset
     .PortNumber "1"
     .Label ""
     .Folder ""
     .NumberOfModes "2"
     .AdjustPolarization "False"
     .PolarizationAngle "0.0"
     .ReferencePlaneDistance "0"
     .TextSize "50"
     .TextMaxLimit "0"
     .Coordinates "Full"
     .Orientation "zmin"
     .PortOnBound "False"
     .ClipPickedPortToBound "False"
     .Xrange "-0.304975", "0.0056"
     .Yrange "-0.25", "0.25"
     .Zrange "0", "0"
     .XrangeAdd "0.0", "0.0"
     .YrangeAdd "0.0", "0.0"
     .ZrangeAdd "0.0", "0.0"
     .SingleEnded "False"
     .WaveguideMonitor "False"
     .Create
End With

' define port: 2
With Port
     .Reset
     .PortNumber "2"
     .Label ""
     .Folder ""
     .NumberOfModes "2"
     .AdjustPolarization "False"
     .PolarizationAngle "0.0"
     .ReferencePlaneDistance "0"
     .TextSize "50"
     .TextMaxLimit "0"
     .Coordinates "Full"
     .Orientation "zmax"
     .PortOnBound "False"
     .ClipPickedPortToBound "False"
     .Xrange "-0.304975", "0.0056"
     .Yrange "-0.25", "0.25"
     .Zrange "0.05", "0.05"
     .XrangeAdd "0.0", "0.0"
     .YrangeAdd "0.0", "0.0"
     .ZrangeAdd "0.0", "0.0"
     .SingleEnded "False"
     .WaveguideMonitor "False"
     .Create
End With

' change solver type
ChangeSolverType "HF Time Domain"

' define time domain solver parameters
Mesh.SetCreator "High Frequency"
With Solver
     .Method "Hexahedral"
     .CalculationType "TD-S"
     .StimulationPort "All"
     .StimulationMode "All"
     .SteadyStateLimit "-40"
     .MeshAdaption "False"
     .AutoNormImpedance "False"
     .NormingImpedance "50"
     .CalculateModesOnly "True"
     .SParaSymmetry "False"
     .StoreTDResultsInCache "False"
     .RunDiscretizerOnly "False"
     .FullDeembedding "False"
     .SuperimposePLWExcitation "False"
     .UseSensitivityAnalysis "False"
End With
