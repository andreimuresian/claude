' Single U-bend (2 straight sections + 1 U-bend): 60 E-field monitors, 1..60 GHz every 1 GHz,
' each on a thin slab (electrode layer x 0..MTX) covering the gaps of both lines and the bend.
' Run once (Macros > Edit/Run). Each monitor is written to the history list, so it survives history rebuilds.
' Names follow the earlier runs: "e-field (f=N)", results appear as "e-field (f=N) [1]".
Sub Main ()
    Dim i As Integer, sName As String, sCmd As String
    For i = 1 To 60
        sName = "e-field (f=" & CStr(i) & ")"
        sCmd = "With Monitor" & vbCrLf & _
               "     .Reset" & vbCrLf & _
               "     .Name """ & sName & """" & vbCrLf & _
               "     .Dimension ""Volume""" & vbCrLf & _
               "     .Domain ""Frequency""" & vbCrLf & _
               "     .FieldType ""Efield""" & vbCrLf & _
               "     .MonitorValue """ & CStr(i) & """" & vbCrLf & _
               "     .UseSubvolume ""True""" & vbCrLf & _
               "     .Coordinates ""Free""" & vbCrLf & _
               "     .SetSubvolume ""0"", ""MTX"", ""-BEND_RADIUS-0.1"", ""BEND_RADIUS+0.1"", ""0"", ""DEV_L""" & vbCrLf & _
               "     .SetSubvolumeOffset ""0"", ""0"", ""0"", ""0"", ""0"", ""0""" & vbCrLf & _
               "     .SetSubvolumeInflateWithOffset ""False""" & vbCrLf & _
               "     .Create" & vbCrLf & _
               "End With"
        AddToHistory "define monitor: " & sName, sCmd
    Next i
End Sub
