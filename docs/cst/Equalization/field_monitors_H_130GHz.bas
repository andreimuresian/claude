' H-field monitors for the 0-130 GHz runs (same frequencies and box as field_monitors_130GHz.bas, which defines the E monitors).
' Frequencies: 1..60 GHz every 1 GHz, then 62..130 GHz every 2 GHz (95 monitors).
' Box: x from 1 um below the buried electrodes to 1 um above the raised ones (-0.001 .. CLAD_H+MTX+0.001), so that a closed
' loop around each signal electrode (buried: x 0..MTX, raised: CLAD_H..CLAD_H+MTX) lies inside the monitor (current = loop integral of H).
' Set Y_MAX for the run before executing:
'   full equaliser : "3*BEND_RADIUS+0.1"     L+B+S and single bend : "BEND_RADIUS+0.1"     L+S : "-BEND_RADIUS+0.1"
' Names: "h-field (f=N)", results appear as "h-field (f=N) [1]" (and [2] if port 2 is also excited).
Const Y_MAX As String = "BEND_RADIUS+0.1"

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
    sName = "h-field (f=" & CStr(f) & ")"
    sCmd = "With Monitor" & vbCrLf & _
           "     .Reset" & vbCrLf & _
           "     .Name """ & sName & """" & vbCrLf & _
           "     .Dimension ""Volume""" & vbCrLf & _
           "     .Domain ""Frequency""" & vbCrLf & _
           "     .FieldType ""Hfield""" & vbCrLf & _
           "     .MonitorValue """ & CStr(f) & """" & vbCrLf & _
           "     .UseSubvolume ""True""" & vbCrLf & _
           "     .Coordinates ""Free""" & vbCrLf & _
           "     .SetSubvolume ""-0.001"", ""CLAD_H+MTX+0.001"", ""-BEND_RADIUS-0.1"", """ & Y_MAX & """, ""0"", ""DEV_L""" & vbCrLf & _
           "     .SetSubvolumeOffset ""0"", ""0"", ""0"", ""0"", ""0"", ""0""" & vbCrLf & _
           "     .SetSubvolumeInflateWithOffset ""False""" & vbCrLf & _
           "     .Create" & vbCrLf & _
           "End With"
    AddToHistory "define monitor: " & sName, sCmd
End Sub
