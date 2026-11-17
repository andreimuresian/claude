' Single straight line (line 1 only), project "BASELINE - L+S - clad digs removed".
' Exports the E-field of monitors "e-field (f=N) [1]" (port 1 excitation), N = 1..60 GHz,
' and writes ONE file per gap containing all frequencies (first column = frequency in GHz).
'
' Coordinates are computed from the project parameters, so they always match the run:
'   line centre y = -BEND_RADIUS, gap centres y = -BEND_RADIUS +/- (WS/2 + GAP/2),
'   x = MTX/2 (mid-height of the electrodes), z = 0 .. EL_L (buried electrode), step 0.005 mm.
' Touchstone header of this run: EL_L = 3.24 (N_CELL 17), DEV_L = 3.74, BEND_RADIUS 0.1025
'   -> gap+ y = -0.082925, gap- y = -0.122075, z 0 .. 3.24.

Option Explicit

Const F_MIN As Integer = 1
Const F_MAX As Integer = 60
Const EXC As String = "[1]"          ' excitation: [1] = port 1
Const STP As Double = 0.005

Sub Main ()
    Dim outDir As String, br As Double, ws As Double, gp As Double, mtx As Double, ell As Double, yc As Double, dy As Double
    br  = RestoreDoubleParameter("BEND_RADIUS")
    ws  = RestoreDoubleParameter("WS")
    gp  = RestoreDoubleParameter("GAP")
    mtx = RestoreDoubleParameter("MTX")
    ell = RestoreDoubleParameter("EL_L")
    yc = -br
    dy = ws / 2 + gp / 2

    outDir = GetProjectPath("Project") & "_field_exports\"
    On Error Resume Next
    MkDir outDir
    On Error GoTo 0

    DoRegion outDir, "L1_gap+", mtx / 2, mtx / 2, yc + dy, yc + dy, 0, ell, STP
    DoRegion outDir, "L1_gap-", mtx / 2, mtx / 2, yc - dy, yc - dy, 0, ell, STP

    MsgBox "Field export finished: " & outDir & vbCrLf & _
           "gap+ y = " & (yc + dy) & ", gap- y = " & (yc - dy) & ", z 0 .. " & ell & " mm"
End Sub

' Exports one region for all frequencies and merges them into <outDir><name>.txt
Sub DoRegion (outDir As String, name As String, _
              x0 As Double, x1 As Double, y0 As Double, y1 As Double, z0 As Double, z1 As Double, stp As Double)
    Dim f As Integer, item As String, tmp As String, merged As String
    Dim fin As Integer, fout As Integer, s As String, t As String, headerDone As Boolean

    merged = outDir & name & ".txt"
    tmp = outDir & "_tmp_export.txt"
    fout = FreeFile
    Open merged For Output As #fout
    Print #fout, "# region " & name & ": x " & x0 & " .. " & x1 & ", y " & y0 & " .. " & y1 & _
                 ", z " & z0 & " .. " & z1 & " mm, step " & stp & " mm, excitation " & EXC
    headerDone = False

    For f = F_MIN To F_MAX
        item = "2D/3D Results\E-Field\e-field (f=" & CStr(f) & ") " & EXC
        If SelectTreeItem(item) = False Then
            ReportWarningToWindow "Missing result: " & item
        Else
            With ASCIIExport
                .Reset
                .FileName tmp
                .SetFileType "txt"
                .Mode "FixedWidth"
                .Step stp
                .UseSubvolume True
                .SetSubvolume x0, x1, y0, y1, z0, z1
                .Execute
            End With

            fin = FreeFile
            Open tmp For Input As #fin
            Do While Not EOF(fin)
                Line Input #fin, s
                t = Trim(s)
                If Len(t) > 0 Then
                    If IsDataRow(t) Then
                        Print #fout, CStr(f) & vbTab & t                       ' data row: f [GHz] then CST columns
                    ElseIf Not headerDone And Left(t, 2) <> "--" Then
                        Print #fout, "f [GHz]" & vbTab & t                     ' column titles, once
                        headerDone = True
                    End If
                End If
            Loop
            Close #fin
        End If
    Next f

    Close #fout
    On Error Resume Next
    Kill tmp
    On Error GoTo 0
End Sub

' True for a numeric data row ("0.001 ...", "-0.08 ..."), false for titles and the dashed separator.
' Character test instead of IsNumeric, so the decimal point is read the same in every Windows locale.
Function IsDataRow (t As String) As Boolean
    Dim c As String
    c = Left(t, 1)
    If c = "-" Or c = "+" Then c = Mid(t, 2, 1)
    IsDataRow = (InStr("0123456789.", c) > 0 And Len(c) = 1)
End Function
