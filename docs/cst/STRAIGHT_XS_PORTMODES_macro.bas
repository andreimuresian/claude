' Straight CPW (bend cross-section), port modes only.
' Run with: Home > Macros > Run Macro... (select this file). Each block is executed and added to the history.
Option Explicit

Sub Main
    Dim s As String
    s = ""
    s = s & "With Units" & vbCrLf
    s = s & "     .SetUnit ""Length"", ""mm""" & vbCrLf
    s = s & "     .SetUnit ""Frequency"", ""GHz""" & vbCrLf
    s = s & "     .SetUnit ""Voltage"", ""V""" & vbCrLf
    s = s & "     .SetUnit ""Resistance"", ""Ohm""" & vbCrLf
    s = s & "     .SetUnit ""Inductance"", ""nH""" & vbCrLf
    s = s & "     .SetUnit ""Temperature"", ""degC""" & vbCrLf
    s = s & "     .SetUnit ""Time"", ""ns""" & vbCrLf
    s = s & "     .SetUnit ""Current"", ""A""" & vbCrLf
    s = s & "     .SetUnit ""Conductance"", ""S""" & vbCrLf
    s = s & "     .SetUnit ""Capacitance"", ""pF""" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define units", s

    s = ""
    s = s & "With Material" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""LN""" & vbCrLf
    s = s & "     .Folder """"" & vbCrLf
    s = s & "     .FrqType ""all""" & vbCrLf
    s = s & "     .Type ""Anisotropic""" & vbCrLf
    s = s & "     .MaterialUnit ""Frequency"", ""GHz""" & vbCrLf
    s = s & "     .MaterialUnit ""Geometry"", ""mm""" & vbCrLf
    s = s & "     .EpsilonX ""43""" & vbCrLf
    s = s & "     .EpsilonY ""28""" & vbCrLf
    s = s & "     .EpsilonZ ""43""" & vbCrLf
    s = s & "     .MuX ""1""" & vbCrLf
    s = s & "     .MuY ""1""" & vbCrLf
    s = s & "     .MuZ ""1""" & vbCrLf
    s = s & "     .Colour ""0"", ""0"", ""0""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define material: LN", s

    s = ""
    s = s & "With Material" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""SIO2""" & vbCrLf
    s = s & "     .Folder """"" & vbCrLf
    s = s & "     .FrqType ""all""" & vbCrLf
    s = s & "     .Type ""Normal""" & vbCrLf
    s = s & "     .Epsilon ""3.9""" & vbCrLf
    s = s & "     .Mu ""1""" & vbCrLf
    s = s & "     .Colour ""0"", ""0"", ""1""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define material: SIO2", s

    s = ""
    s = s & "With Material" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""Silicon (lossy)""" & vbCrLf
    s = s & "     .Folder """"" & vbCrLf
    s = s & "     .FrqType ""all""" & vbCrLf
    s = s & "     .Type ""Normal""" & vbCrLf
    s = s & "     .SetMaterialUnit ""GHz"", ""mm""" & vbCrLf
    s = s & "     .Epsilon ""11.9""" & vbCrLf
    s = s & "     .Mu ""1.0""" & vbCrLf
    s = s & "     .Kappa ""2.5e-004""" & vbCrLf
    s = s & "     .Colour ""0.666667"", ""0.666667"", ""1""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define material: Silicon (lossy)", s

    s = ""
    s = s & "With Material" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""Gold""" & vbCrLf
    s = s & "     .Folder """"" & vbCrLf
    s = s & "     .FrqType ""all""" & vbCrLf
    s = s & "     .Type ""Lossy metal""" & vbCrLf
    s = s & "     .MaterialUnit ""Frequency"", ""GHz""" & vbCrLf
    s = s & "     .MaterialUnit ""Geometry"", ""mm""" & vbCrLf
    s = s & "     .Mu ""1.0""" & vbCrLf
    s = s & "     .Sigma ""4.561e+007""" & vbCrLf
    s = s & "     .Rho ""19320.0""" & vbCrLf
    s = s & "     .Colour ""1"", ""1"", ""0""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define material: Gold", s

    s = ""
    s = s & "Component.New ""component1""" & vbCrLf
    AddToHistory "new component: component1", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""si""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""Silicon (lossy)""" & vbCrLf
    s = s & "     .Xrange ""-0.304975"", ""-0.004975""" & vbCrLf
    s = s & "     .Yrange ""-0.25"", ""0.25""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:si", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""box""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""SIO2""" & vbCrLf
    s = s & "     .Xrange ""-0.004975"", ""-0.000275""" & vbCrLf
    s = s & "     .Yrange ""-0.25"", ""0.25""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:box", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""slab""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""LN""" & vbCrLf
    s = s & "     .Xrange ""-0.000275"", ""0""" & vbCrLf
    s = s & "     .Yrange ""-0.25"", ""0.25""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:slab", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""cap""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""SIO2""" & vbCrLf
    s = s & "     .Xrange ""0"", ""0.0036""" & vbCrLf
    s = s & "     .Yrange ""-0.25"", ""0.25""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:cap", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""signal""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""Gold""" & vbCrLf
    s = s & "     .Xrange ""0.0036"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""-0.0175"", ""0.0175""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:signal", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""ground_r""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""Gold""" & vbCrLf
    s = s & "     .Xrange ""0.0036"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""0.022"", ""0.07185""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:ground_r", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""ground_l""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""Gold""" & vbCrLf
    s = s & "     .Xrange ""0.0036"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""-0.07185"", ""-0.022""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:ground_l", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""gap_r""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""Vacuum""" & vbCrLf
    s = s & "     .Xrange ""0.0036"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""0.0175"", ""0.022""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:gap_r", s

    s = ""
    s = s & "With Brick" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .Name ""gap_l""" & vbCrLf
    s = s & "     .Component ""component1""" & vbCrLf
    s = s & "     .Material ""Vacuum""" & vbCrLf
    s = s & "     .Xrange ""0.0036"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""-0.022"", ""-0.0175""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0.05""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define brick: component1:gap_l", s

    s = ""
    s = s & "Group.Add ""meshgroup_xs"", ""mesh""" & vbCrLf
    AddToHistory "create group: meshgroup_xs", s

    s = ""
    s = s & "Group.AddItem ""solid$component1:signal"", ""meshgroup_xs""" & vbCrLf
    s = s & "Group.AddItem ""solid$component1:ground_r"", ""meshgroup_xs""" & vbCrLf
    s = s & "Group.AddItem ""solid$component1:ground_l"", ""meshgroup_xs""" & vbCrLf
    s = s & "Group.AddItem ""solid$component1:gap_r"", ""meshgroup_xs""" & vbCrLf
    s = s & "Group.AddItem ""solid$component1:gap_l"", ""meshgroup_xs""" & vbCrLf
    AddToHistory "add items to group: meshgroup_xs", s

    s = ""
    s = s & "Solver.FrequencyRange ""59.9"", ""60""" & vbCrLf
    AddToHistory "define frequency range", s

    s = ""
    s = s & "With Background" & vbCrLf
    s = s & "     .ResetBackground" & vbCrLf
    s = s & "     .XminSpace ""0.0""" & vbCrLf
    s = s & "     .XmaxSpace ""0.05""" & vbCrLf
    s = s & "     .YminSpace ""0.0""" & vbCrLf
    s = s & "     .YmaxSpace ""0.0""" & vbCrLf
    s = s & "     .ZminSpace ""0.0""" & vbCrLf
    s = s & "     .ZmaxSpace ""0.0""" & vbCrLf
    s = s & "     .ApplyInAllDirections ""False""" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define background", s

    s = ""
    s = s & "With Boundary" & vbCrLf
    s = s & "     .Xmin ""open""" & vbCrLf
    s = s & "     .Xmax ""open""" & vbCrLf
    s = s & "     .Ymin ""open""" & vbCrLf
    s = s & "     .Ymax ""open""" & vbCrLf
    s = s & "     .Zmin ""open""" & vbCrLf
    s = s & "     .Zmax ""open""" & vbCrLf
    s = s & "     .Xsymmetry ""none""" & vbCrLf
    s = s & "     .Ysymmetry ""none""" & vbCrLf
    s = s & "     .Zsymmetry ""none""" & vbCrLf
    s = s & "     .ApplyInAllDirections ""True""" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define boundaries", s

    s = ""
    s = s & "With Mesh" & vbCrLf
    s = s & "     .MeshType ""PBA""" & vbCrLf
    s = s & "     .SetCreator ""High Frequency""" & vbCrLf
    s = s & "End With" & vbCrLf
    s = s & "With MeshSettings" & vbCrLf
    s = s & "     .SetMeshType ""Hex""" & vbCrLf
    s = s & "     .Set ""Version"", 1%" & vbCrLf
    s = s & "     .Set ""StepsPerWaveNear"", ""50""" & vbCrLf
    s = s & "     .Set ""StepsPerWaveFar"", ""50""" & vbCrLf
    s = s & "     .Set ""WavelengthRefinementSameAsNear"", ""1""" & vbCrLf
    s = s & "     .Set ""StepsPerBoxNear"", ""50""" & vbCrLf
    s = s & "     .Set ""StepsPerBoxFar"", ""50""" & vbCrLf
    s = s & "     .Set ""MaxStepNear"", ""0""" & vbCrLf
    s = s & "     .Set ""MaxStepFar"", ""0""" & vbCrLf
    s = s & "     .Set ""ModelBoxDescrNear"", ""maxedge""" & vbCrLf
    s = s & "     .Set ""ModelBoxDescrFar"", ""maxedge""" & vbCrLf
    s = s & "     .Set ""UseMaxStepAbsolute"", ""0""" & vbCrLf
    s = s & "     .Set ""GeometryRefinementSameAsNear"", ""1""" & vbCrLf
    s = s & "     .Set ""UseRatioLimitGeometry"", ""1""" & vbCrLf
    s = s & "     .Set ""RatioLimitGeometry"", ""50""" & vbCrLf
    s = s & "     .Set ""MinStepGeometryX"", ""0""" & vbCrLf
    s = s & "     .Set ""MinStepGeometryY"", ""0""" & vbCrLf
    s = s & "     .Set ""MinStepGeometryZ"", ""0""" & vbCrLf
    s = s & "     .Set ""UseSameMinStepGeometryXYZ"", ""1""" & vbCrLf
    s = s & "End With" & vbCrLf
    s = s & "With MeshSettings" & vbCrLf
    s = s & "     .SetMeshType ""Hex""" & vbCrLf
    s = s & "     .Set ""EdgeRefinementType"", ""RATIO""" & vbCrLf
    s = s & "     .Set ""EdgeRefinementRatio"", ""2""" & vbCrLf
    s = s & "     .Set ""EdgeRefinementStep"", ""0""" & vbCrLf
    s = s & "     .Set ""EdgeRefinementBufferLines"", ""3""" & vbCrLf
    s = s & "     .Set ""BufferLinesNear"", ""3""" & vbCrLf
    s = s & "     .Set ""UseDielectrics"", ""1""" & vbCrLf
    s = s & "     .Set ""EquilibrateOn"", ""1""" & vbCrLf
    s = s & "     .Set ""Equilibrate"", ""1.5""" & vbCrLf
    s = s & "     .Set ""IgnoreThinPanelMaterial"", ""0""" & vbCrLf
    s = s & "End With" & vbCrLf
    s = s & "With Mesh" & vbCrLf
    s = s & "     .ConnectivityCheck ""True""" & vbCrLf
    s = s & "     .UsePecEdgeModel ""True""" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "set mesh properties (Hexahedral FIT)", s

    s = ""
    s = s & "With Port" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .PortNumber ""1""" & vbCrLf
    s = s & "     .Label """"" & vbCrLf
    s = s & "     .Folder """"" & vbCrLf
    s = s & "     .NumberOfModes ""2""" & vbCrLf
    s = s & "     .AdjustPolarization ""False""" & vbCrLf
    s = s & "     .PolarizationAngle ""0.0""" & vbCrLf
    s = s & "     .ReferencePlaneDistance ""0""" & vbCrLf
    s = s & "     .TextSize ""50""" & vbCrLf
    s = s & "     .TextMaxLimit ""0""" & vbCrLf
    s = s & "     .Coordinates ""Full""" & vbCrLf
    s = s & "     .Orientation ""zmin""" & vbCrLf
    s = s & "     .PortOnBound ""False""" & vbCrLf
    s = s & "     .ClipPickedPortToBound ""False""" & vbCrLf
    s = s & "     .Xrange ""-0.304975"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""-0.25"", ""0.25""" & vbCrLf
    s = s & "     .Zrange ""0"", ""0""" & vbCrLf
    s = s & "     .XrangeAdd ""0.0"", ""0.0""" & vbCrLf
    s = s & "     .YrangeAdd ""0.0"", ""0.0""" & vbCrLf
    s = s & "     .ZrangeAdd ""0.0"", ""0.0""" & vbCrLf
    s = s & "     .SingleEnded ""False""" & vbCrLf
    s = s & "     .WaveguideMonitor ""False""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define port: 1", s

    s = ""
    s = s & "With Port" & vbCrLf
    s = s & "     .Reset" & vbCrLf
    s = s & "     .PortNumber ""2""" & vbCrLf
    s = s & "     .Label """"" & vbCrLf
    s = s & "     .Folder """"" & vbCrLf
    s = s & "     .NumberOfModes ""2""" & vbCrLf
    s = s & "     .AdjustPolarization ""False""" & vbCrLf
    s = s & "     .PolarizationAngle ""0.0""" & vbCrLf
    s = s & "     .ReferencePlaneDistance ""0""" & vbCrLf
    s = s & "     .TextSize ""50""" & vbCrLf
    s = s & "     .TextMaxLimit ""0""" & vbCrLf
    s = s & "     .Coordinates ""Full""" & vbCrLf
    s = s & "     .Orientation ""zmax""" & vbCrLf
    s = s & "     .PortOnBound ""False""" & vbCrLf
    s = s & "     .ClipPickedPortToBound ""False""" & vbCrLf
    s = s & "     .Xrange ""-0.304975"", ""0.0056""" & vbCrLf
    s = s & "     .Yrange ""-0.25"", ""0.25""" & vbCrLf
    s = s & "     .Zrange ""0.05"", ""0.05""" & vbCrLf
    s = s & "     .XrangeAdd ""0.0"", ""0.0""" & vbCrLf
    s = s & "     .YrangeAdd ""0.0"", ""0.0""" & vbCrLf
    s = s & "     .ZrangeAdd ""0.0"", ""0.0""" & vbCrLf
    s = s & "     .SingleEnded ""False""" & vbCrLf
    s = s & "     .WaveguideMonitor ""False""" & vbCrLf
    s = s & "     .Create" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define port: 2", s

    s = ""
    s = s & "ChangeSolverType ""HF Time Domain""" & vbCrLf
    AddToHistory "change solver type", s

    s = ""
    s = s & "Mesh.SetCreator ""High Frequency""" & vbCrLf
    s = s & "With Solver" & vbCrLf
    s = s & "     .Method ""Hexahedral""" & vbCrLf
    s = s & "     .CalculationType ""TD-S""" & vbCrLf
    s = s & "     .StimulationPort ""All""" & vbCrLf
    s = s & "     .StimulationMode ""All""" & vbCrLf
    s = s & "     .SteadyStateLimit ""-40""" & vbCrLf
    s = s & "     .MeshAdaption ""False""" & vbCrLf
    s = s & "     .AutoNormImpedance ""False""" & vbCrLf
    s = s & "     .NormingImpedance ""50""" & vbCrLf
    s = s & "     .CalculateModesOnly ""True""" & vbCrLf
    s = s & "     .SParaSymmetry ""False""" & vbCrLf
    s = s & "     .StoreTDResultsInCache ""False""" & vbCrLf
    s = s & "     .RunDiscretizerOnly ""False""" & vbCrLf
    s = s & "     .FullDeembedding ""False""" & vbCrLf
    s = s & "     .SuperimposePLWExcitation ""False""" & vbCrLf
    s = s & "     .UseSensitivityAnalysis ""False""" & vbCrLf
    s = s & "End With" & vbCrLf
    AddToHistory "define time domain solver parameters", s

End Sub
