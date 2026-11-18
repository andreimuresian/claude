' E-field monitors for the 0-130 GHz reruns (full equaliser, L+S, L+B+S).
' Frequencies: 1..60 GHz every 1 GHz, then 62..130 GHz every 2 GHz (95 monitors).
' Subvolume x 0 .. CLAD_H+MTX: buried electrodes (0 .. MTX) AND raised tapers/bends (CLAD_H .. CLAD_H+MTX).
' Set Y_MAX for the run before executing:
'   full equaliser : "3*BEND_RADIUS+0.1"     L+B+S : "BEND_RADIUS+0.1"     L+S : "-BEND_RADIUS+0.1"
' Names follow the earlier runs ("e-field (f=N)"), so the export macros work unchanged.
Const Y_MAX As String = "3*BEND_RADIUS+0.1"

Sub Main ()
    Dim f As Integer
    For f = 1 To 60
        AddMon f
    Next f
    For f = 62 To 130 Step 2
        AddMon f
    Next f
End Sub

Sub AddMon (f As Integer)
    Dim sName As String, sCmd As String
    sName = "e-field (f=" & CStr(f) & ")"
    sCmd = "With Monitor" & vbCrLf & _
           "     .Reset" & vbCrLf & _
           "     .Name """ & sName & """" & vbCrLf & _
           "     .Dimension ""Volume""" & vbCrLf & _
           "     .Domain ""Frequency""" & vbCrLf & _
           "     .FieldType ""Efield""" & vbCrLf & _
           "     .MonitorValue """ & CStr(f) & """" & vbCrLf & _
           "     .UseSubvolume ""True""" & vbCrLf & _
           "     .Coordinates ""Free""" & vbCrLf & _
           "     .SetSubvolume ""0"", ""CLAD_H+MTX"", ""-BEND_RADIUS-0.1"", """ & Y_MAX & """, ""0"", ""DEV_L""" & vbCrLf & _
           "     .SetSubvolumeOffset ""0"", ""0"", ""0"", ""0"", ""0"", ""0""" & vbCrLf & _
           "     .SetSubvolumeInflateWithOffset ""False""" & vbCrLf & _
           "     .Create" & vbCrLf & _
           "End With"
    AddToHistory "define monitor: " & sName, sCmd
End Sub
